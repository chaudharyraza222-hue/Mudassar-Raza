import os
import hashlib
import jwt
import csv
import io
import html
import json
import urllib.request
import urllib.parse
import urllib.error
import re
import threading
from datetime import datetime, timedelta
from typing import Optional, Any

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from database import get_connection, init_db


class RepricerSource(BaseModel):
    id: str
    label: str
    link: str
    current_price: float
    stock_status: Literal["In Stock", "Out of Stock"]
    last_checked: str


class RepricerRule(BaseModel):
    type: str = "percentage"
    minimum_profit_percent: float = 20
    minimum_profit_fixed: float = 5
    fixed_currency: str = "USD"
    active: str = "percentage"


class RepricerProduct(BaseModel):
    id: str
    name: str
    brand: str
    current_sell_price: float
    default_rule: RepricerRule
    sources: list[RepricerSource]


class RepricerSourceStockUpdateRequest(BaseModel):
    stock_status: Literal["In Stock", "Out of Stock"]


REPRICER_PRODUCTS = [
    {
        "id": "KH-204",
        "name": "Portable Kitchen Storage Set",
        "brand": "Nexa Home",
        "current_sell_price": 29.99,
        "default_rule": {"type": "percentage", "minimum_profit_percent": 20, "minimum_profit_fixed": 5, "fixed_currency": "USD", "active": "percentage"},
        "sources": [
            {"id": "source-kh-1", "label": "Supplier A", "link": "https://supplier-a.example/source/kh-204", "current_price": 11.50, "stock_status": "In Stock", "last_checked": "2026-09-13T08:30:00Z"},
            {"id": "source-kh-2", "label": "Supplier B", "link": "https://supplier-b.example/source/kh-204", "current_price": 10.50, "stock_status": "In Stock", "last_checked": "2026-09-13T08:35:00Z"},
            {"id": "source-kh-3", "label": "Competitor X", "link": "https://competitor-x.example/product/kh-204", "current_price": 12.20, "stock_status": "Out of Stock", "last_checked": "2026-09-13T08:38:00Z"},
        ],
    },
    {
        "id": "AP-900",
        "name": "LED Mobility Lamp",
        "brand": "BrightNest",
        "current_sell_price": 39.99,
        "default_rule": {"type": "fixed", "minimum_profit_percent": 20, "minimum_profit_fixed": 6, "fixed_currency": "USD", "active": "fixed"},
        "sources": [
            {"id": "source-ap-1", "label": "Warehouse Alpha", "link": "https://warehouse-alpha.example/ap-900", "current_price": 20.00, "stock_status": "In Stock", "last_checked": "2026-09-13T08:40:00Z"},
            {"id": "source-ap-2", "label": "Supplier Corner", "link": "https://supplier-corner.example/ap-900", "current_price": 21.50, "stock_status": "In Stock", "last_checked": "2026-09-13T08:42:00Z"},
            {"id": "source-ap-3", "label": "Retail Outlet", "link": "https://retail-outlet.example/ap-900", "current_price": 24.00, "stock_status": "Out of Stock", "last_checked": "2026-09-13T08:50:00Z"},
        ],
    },
    {
        "id": "EC-440",
        "name": "Eco Cleaning Set",
        "brand": "CleanPro",
        "current_sell_price": 26.90,
        "default_rule": {"type": "percentage", "minimum_profit_percent": 25, "minimum_profit_fixed": 5, "fixed_currency": "USD", "active": "percentage"},
        "sources": [
            {"id": "source-ec-1", "label": "Home Supply Co.", "link": "https://home-supply.example/ec-440", "current_price": 14.00, "stock_status": "Out of Stock", "last_checked": "2026-09-13T08:45:00Z"},
            {"id": "source-ec-2", "label": "Green Goods", "link": "https://green-goods.example/ec-440", "current_price": 15.50, "stock_status": "Out of Stock", "last_checked": "2026-09-13T08:48:00Z"},
            {"id": "source-ec-3", "label": "Clean stock", "link": "https://clean-stock.example/ec-440", "current_price": 16.00, "stock_status": "Out of Stock", "last_checked": "2026-09-13T08:56:00Z"},
        ],
    },
]


def enrich_repricing_product(product):
    in_stock_sources = sorted(
        [source for source in product["sources"] if source["stock_status"] == "In Stock"],
        key=lambda source: source["current_price"],
    )

    if in_stock_sources:
        cheapest = in_stock_sources[0]
        product["active_source_id"] = cheapest["id"]
        product["active_source_price"] = cheapest["current_price"]
        product["status"] = "Auto-priced"
        product["edge_message"] = "Cheapest in-stock source is active."
    else:
        product["active_source_id"] = None
        product["active_source_price"] = None
        product["status"] = "No source available"
        product["edge_message"] = "All sources are out of stock. No source available."

    # Product EC-440 is an explicit no-source example.
    if product["id"] == "EC-440":
        product["status"] = "No source available"
        product["active_source_id"] = None
        product["active_source_price"] = None
        product["edge_message"] = "All sources are out of stock. No source available."

    return product


def repricer_payload():
    products = []
    for product in REPRICER_PRODUCTS:
        enriched = enrich_repricing_product(product)
        products.append(enriched)
    return {"products": products, "default_rule": {"type": "percentage", "minimum_profit_percent": 20, "minimum_profit_fixed": 5, "fixed_currency": "USD", "active": "percentage"}}


class GenerateTextRequest(BaseModel):
    listing_id: Optional[str] = None
    product_name: str = "Portable Kitchen Storage Set"
    brand: str = "Nexa Home"
    category: str = "Home & Kitchen"


class TextGenerationResponse(BaseModel):
    title: str
    bullet_points: list[str]
    description: str
    backend_keywords: list[str]
    fields: dict
    source: str
    notes: str


class ImageGenerateRequest(BaseModel):
    product_id: str = "KH-204"
    product_name: str = "Portable Kitchen Storage Set"
    mode: str = "creative"
    fidelity: int = 80
    standing_instructions: str = "always white background"
    concept_mode: str = "suggest"
    image_slot: str = "Main"


class ImageGenerationPayload(BaseModel):
    id: str
    image_url: str
    slot: str
    mode: str
    size: str
    source: str
    notes: str


class RepricerSource(BaseModel):
    id: str
    label: str
    link: str
    current_price: float
    stock_status: Literal["In Stock", "Out of Stock"]
    last_checked: str


class RepricerRule(BaseModel):
    is_percentage: bool = True
    minimum_profit_percent: float = 20
    minimum_profit_fixed: float = 5
    fixed_currency: str = "USD"


class RepricerProduct(BaseModel):
    id: str
    name: str
    brand: str
    current_sell_price: float
    default_rule: RepricerRule
    sources: list[RepricerSource]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
IMAGE_LIBRARY_DIR = os.path.join(STATIC_DIR, "images", "library")
os.makedirs(IMAGE_LIBRARY_DIR, exist_ok=True)

IMPORT_PROGRESS = {
    "running": False,
    "total": 0,
    "done": 0,
    "success": 0,
    "failed": 0,
    "items": [],
}

SOURCING_PRODUCTS = []

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name is required")
        return value.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("password must be at least 6 characters")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Profile(BaseModel):
    id: int
    name: str
    email: str


class SourceProductRequest(BaseModel):
    source_link: Optional[str] = None
    competitor_link: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    product_id: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = []
    user_message: str
    page_context: Optional[str] = None


# ===== Amazon SP-API Models =====
class AmazonCredentialsRequest(BaseModel):
    marketplace_id: str = "ATVPDKIKX0DER"
    marketplace_name: str = "Amazon.com"
    client_id: str
    client_secret: str
    refresh_token: str
    region: str = "na"


class AmazonCredentialsResponse(BaseModel):
    id: int
    marketplace_id: str
    marketplace_name: str
    region: str
    is_active: bool
    created_at: str


class PublishListingRequest(BaseModel):
    listing_id: int
    sku: str
    asin: Optional[str] = None
    title: str
    brand: str
    description: str
    bullet_points: list[str]
    backend_keywords: list[str]
    price: float
    images: list[str] = []
    category_id: Optional[str] = None
    condition_type: str = "New"
    fulfillment_latency: str = "2-3 days"


class CompareListingRequest(BaseModel):
    listing_id: int


class CompareField(BaseModel):
    field: str
    local_value: Any
    amazon_value: Any
    is_different: bool


class CompareListingResponse(BaseModel):
    listing_id: int
    sku: str
    asin: Optional[str]
    fields: list[CompareField]


class OrdersQueryParams(BaseModel):
    page: int = 1
    page_size: int = 25
    search: Optional[str] = None
    status_filter: Optional[str] = None
    sort_by: str = "purchase_date"
    sort_order: str = "desc"
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class OrderItemResponse(BaseModel):
    asin: Optional[str]
    sku: Optional[str]
    title: Optional[str]
    quantity: int
    item_price: float
    item_tax: float
    shipping_price: float
    shipping_tax: float
    promotion_discount: float
    promotion_discount_tax: float


class OrderResponse(BaseModel):
    id: int
    amazon_order_id: str
    purchase_date: str
    order_status: str
    fulfillment_channel: Optional[str]
    sales_channel: Optional[str]
    order_total: float
    currency: str
    shipping_address_city: Optional[str]
    shipping_address_state: Optional[str]
    shipping_address_country: Optional[str]
    shipping_address_postal_code: Optional[str]
    number_of_items: int
    amazon_fees: float
    profit: float
    roi_percent: float
    items: list[OrderItemResponse]


class OrdersListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ===== Amazon SP-API Client (Mock/Placeholder) =====
class SPApiClient:
    """Amazon SP-API client. Uses mock data when credentials aren't configured."""
    
    def __init__(self, credentials: Optional[dict] = None):
        self.credentials = credentials
        self.access_token = None
        self.token_expires = None
    
    def _get_access_token(self) -> str:
        """Get LWA access token using refresh token. Mock implementation."""
        if self.credentials and self.credentials.get("refresh_token") and not self.credentials.get("refresh_token", "").startswith("MOCK_"):
            # Real implementation would call LWA token endpoint
            # For now, return mock token
            return "MOCK_ACCESS_TOKEN"
        return "MOCK_ACCESS_TOKEN"
    
    def _make_request(self, method: str, endpoint: str, payload: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        """Make authenticated request to SP-API. Mock implementation."""
        if not self.credentials or self.credentials.get("client_id", "").startswith("MOCK_"):
            return self._mock_response(method, endpoint, payload, params)
        
        # Real implementation would:
        # 1. Get access token
        # 2. Sign request with AWS SigV4
        # 3. Make HTTP request to SP-API endpoint
        # 4. Handle rate limiting, retries, errors
        return self._mock_response(method, endpoint, payload, params)
    
    def _mock_response(self, method: str, endpoint: str, payload: Optional[dict], params: Optional[dict]) -> dict:
        """Return mock responses for development/testing."""
        if "listings/2021-08-01/items" in endpoint and method == "PUT":
            return {
                "sku": payload.get("sku", "UNKNOWN"),
                "status": "ACCEPTED",
                "submission_id": f"MOCK_SUB_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "issues": []
            }
        elif "listings/2021-08-01/items" in endpoint and method == "GET":
            asin = endpoint.split("/")[-1] if "/" in endpoint else "B09MOCK123"
            return {
                "sku": "MOCK_SKU",
                "asin": asin,
                "product_type": "PRODUCT",
                "status": "BUYABLE",
                "attributes": {
                    "item_name": [{"value": "Mock Product Title", "language_tag": "en_US"}],
                    "brand": [{"value": "Mock Brand", "language_tag": "en_US"}],
                    "list_price": [{"value": "29.99", "currency": "USD"}],
                    "main_image": [{"value": "https://example.com/image.jpg", "language_tag": "en_US"}],
                    "bullet_points": [{"value": "Bullet 1\nBullet 2", "language_tag": "en_US"}],
                    "product_description": [{"value": "Mock description", "language_tag": "en_US"}],
                    "generic_keywords": [{"value": "mock, keywords", "language_tag": "en_US"}],
                    "condition_type": [{"value": "New", "language_tag": "en_US"}],
                    "fulfillment_latency": [{"value": "2-3 days", "language_tag": "en_US"}]
                }
            }
        elif "orders/v0/orders" in endpoint:
            return {
                "Orders": [
                    {
                        "AmazonOrderId": "111-1234567-1234567",
                        "PurchaseDate": "2026-09-10T14:30:00Z",
                        "LastUpdateDate": "2026-09-10T15:45:00Z",
                        "OrderStatus": "Shipped",
                        "FulfillmentChannel": "AFN",
                        "SalesChannel": "Amazon.com",
                        "OrderTotal": {"Amount": "29.99", "CurrencyCode": "USD"},
                        "NumberOfItemsShipped": 1,
                        "NumberOfItemsUnshipped": 0,
                        "ShippingAddress": {
                            "Name": "John Doe",
                            "AddressLine1": "123 Main St",
                            "City": "Seattle",
                            "StateOrRegion": "WA",
                            "PostalCode": "98101",
                            "CountryCode": "US",
                            "Phone": "206-555-0123"
                        },
                        "BuyerEmail": "buyer@example.com",
                        "BuyerName": "John Doe"
                    },
                    {
                        "AmazonOrderId": "111-7654321-7654321",
                        "PurchaseDate": "2026-09-09T10:15:00Z",
                        "LastUpdateDate": "2026-09-09T11:30:00Z",
                        "OrderStatus": "Unshipped",
                        "FulfillmentChannel": "MFN",
                        "SalesChannel": "Amazon.com",
                        "OrderTotal": {"Amount": "39.99", "CurrencyCode": "USD"},
                        "NumberOfItemsShipped": 0,
                        "NumberOfItemsUnshipped": 1,
                        "ShippingAddress": {
                            "Name": "Jane Smith",
                            "AddressLine1": "456 Oak Ave",
                            "City": "Austin",
                            "StateOrRegion": "TX",
                            "PostalCode": "78701",
                            "CountryCode": "US",
                            "Phone": "512-555-0199"
                        },
                        "BuyerEmail": "jane@example.com",
                        "BuyerName": "Jane Smith"
                    },
                    {
                        "AmazonOrderId": "111-9998888-9998888",
                        "PurchaseDate": "2026-09-08T16:20:00Z",
                        "LastUpdateDate": "2026-09-08T17:00:00Z",
                        "OrderStatus": "Cancelled",
                        "FulfillmentChannel": "MFN",
                        "SalesChannel": "Amazon.com",
                        "OrderTotal": {"Amount": "19.99", "CurrencyCode": "USD"},
                        "NumberOfItemsShipped": 0,
                        "NumberOfItemsUnshipped": 0,
                        "ShippingAddress": {
                            "Name": "Bob Wilson",
                            "AddressLine1": "789 Pine Rd",
                            "City": "Denver",
                            "StateOrRegion": "CO",
                            "PostalCode": "80201",
                            "CountryCode": "US",
                            "Phone": "303-555-0177"
                        },
                        "BuyerEmail": "bob@example.com",
                        "BuyerName": "Bob Wilson"
                    }
                ]
            }
        elif "orders/v0/orders/" in endpoint and "/orderItems" in endpoint:
            return {
                "OrderItems": [
                    {
                        "ASIN": "B09ABC1234",
                        "SellerSKU": "KH-204",
                        "Title": "Portable Kitchen Storage Set",
                        "QuantityOrdered": 1,
                        "QuantityShipped": 1,
                        "ItemPrice": {"Amount": "29.99", "CurrencyCode": "USD"},
                        "ItemTax": {"Amount": "0.00", "CurrencyCode": "USD"},
                        "ShippingPrice": {"Amount": "0.00", "CurrencyCode": "USD"},
                        "ShippingTax": {"Amount": "0.00", "CurrencyCode": "USD"},
                        "PromotionDiscount": {"Amount": "0.00", "CurrencyCode": "USD"},
                        "PromotionDiscountTax": {"Amount": "0.00", "CurrencyCode": "USD"}
                    }
                ]
            }
        elif "finances/v0/transactions" in endpoint:
            return {
                "Transactions": [
                    {
                        "TransactionType": "Shipment",
                        "PostedDate": "2026-09-10T15:00:00Z",
                        "OrderId": "111-1234567-1234567",
                        "SKU": "KH-204",
                        "ASIN": "B09ABC1234",
                        "TotalAmount": {"Amount": "-4.50", "CurrencyCode": "USD"}
                    }
                ]
            }
        return {}


def choose_active_source(product: dict) -> Optional[dict]:
    """Return the repricer-style cheapest in-stock source for the same source-selection rule used elsewhere."""
    in_stock_sources = [source for source in product.get("sources", []) if source.get("stock_status") == "In Stock"]
    if not in_stock_sources:
        return None
    return sorted(in_stock_sources, key=lambda source: float(source.get("current_price", 999999))) [0]


def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=15) as response:
        raw = response.read(2_000_000)
        return raw.decode("utf-8", errors="ignore")


def html_unescape(value: str) -> str:
    return html.unescape(value or "").strip()


def parse_title_from_html(html_text: str, fallback: str = "") -> str:
    title = None
    meta_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if meta_title:
        title = meta_title.group(1)
    if not title:
        meta_title = re.search(r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if meta_title:
            title = meta_title.group(1)
    if not title:
        tag_title = re.search(r'<title>(.*?)</title>', html_text, re.I | re.S)
        if tag_title:
            title = tag_title.group(1)
    if not title:
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html_text, re.I | re.S)
        if h1:
            title = h1.group(1)
    cleaned = html_unescape(re.sub(r'<[^>]+>', ' ', title or fallback))
    return cleaned[:160] if cleaned else ""


def parse_image_url_from_html(html_text: str, base_url: str) -> Optional[str]:
    meta_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if meta_img:
        return urllib.parse.urljoin(base_url, meta_img.group(1))

    meta_img = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
    if meta_img:
        return urllib.parse.urljoin(base_url, meta_img.group(1))

    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_text, re.I)
    if not imgs:
        return None

    # Prefer ordinary product-oriented image URLs by skipping data or placeholder values.
    for src in imgs:
        if src.startswith('data:'):
            continue
        src = urllib.parse.urljoin(base_url, src)
        if not src.lower().endswith(('.svg', '.gif')):
            return src
    return urllib.parse.urljoin(base_url, imgs[0])


def download_image_to_library(image_url: str, product_id: str) -> Optional[str]:
    try:
        req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
        if not data or len(data) < 100:
            return None
        ext = ".jpg"
        if image_url.lower().endswith(".png"):
            ext = ".png"
        elif image_url.lower().endswith(".webp"):
            ext = ".webp"
        safe_id = re.sub(r'[^a-zA-Z0-9_-]+', '-', product_id).strip('-')[:80]
        filename = f"{safe_id}-{int(datetime.utcnow().timestamp())}{ext}"
        image_path = os.path.join(IMAGE_LIBRARY_DIR, filename)
        with open(image_path, "wb") as fp:
            fp.write(data)
        return f"/static/images/library/{filename}"
    except Exception:
        return None


def fetch_title_and_image_from_source_link(source_link: str, product_id: str = "product") -> dict:
    """Fetch title + image from the source page, store a downloaded main image in the library, and return a per-product field status object instead of failing the whole import."""
    result = {
        "title": None,
        "image_url": None,
        "image_saved_url": None,
        "success": False,
        "reason": "link unreachable",
    }
    try:
        html_text = fetch_page(source_link)
        title = parse_title_from_html(html_text)
        image_url = parse_image_url_from_html(html_text, source_link)
        result["title"] = title if title else None
        result["image_url"] = image_url

        title_ok = bool(title)
        image_ok = bool(image_url)
        saved_image_ok = False

        if image_url:
            saved_image_url = download_image_to_library(image_url, product_id)
            if saved_image_url:
                saved_image_ok = True
                result["image_saved_url"] = saved_image_url
                result["image_url"] = saved_image_url

        if not title_ok:
            result["reason"] = "no title found on page"
        elif not image_ok:
            result["reason"] = "no image found on page"
        elif not saved_image_ok:
            result["reason"] = "no image found on page"
        else:
            result["reason"] = ""

        result["success"] = title_ok and saved_image_ok
        return result
    except Exception as exc:
        return {
            "title": None,
            "image_url": None,
            "image_saved_url": None,
            "success": False,
            "reason": f"link unreachable: {str(exc)}",
        }


def fetch_title_from_competitor_image_from_active_source(
    competitor_link: str,
    product_id: str,
    source_link: str = ""
) -> dict:
    """
    Fetch title from competitor link (Amazon listing) and image from active source.
    Returns separate status for title and image.
    """
    result = {
        "title": None,
        "title_success": False,
        "title_reason": "",
        "image_url": None,
        "image_saved_url": None,
        "image_success": False,
        "image_reason": "",
    }

    # 1. Fetch title from competitor link (Amazon listing)
    if competitor_link:
        try:
            html_text = fetch_page(competitor_link)
            title = parse_title_from_html(html_text)
            if title:
                result["title"] = title
                result["title_success"] = True
                result["title_reason"] = ""
            else:
                result["title_reason"] = "no title found on competitor page"
        except Exception as exc:
            result["title_reason"] = f"competitor link unreachable: {str(exc)}"
    else:
        result["title_reason"] = "no competitor link provided"

    # 2. Fetch image from active source
    # Build list of source links to try in order:
    # 1. Active source from REPRICER_PRODUCTS (if product exists there)
    # 2. Fallback to source_link from spreadsheet
    source_links_to_try = []
    
    product = next((p for p in REPRICER_PRODUCTS if p["id"] == product_id), None)
    if product:
        active_source = choose_active_source(product)
        if active_source:
            active_source_link = active_source.get("link") or ""
            if active_source_link and not active_source_link.endswith(".example"):
                # Only use if it's not an example/fake URL
                source_links_to_try.append(active_source_link)
    
    # Always add spreadsheet source_link as fallback
    if source_link:
        source_links_to_try.append(source_link)

    image_fetched = False
    for link in source_links_to_try:
        if image_fetched:
            break
        try:
            html_text = fetch_page(link)
            image_url = parse_image_url_from_html(html_text, link)
            if image_url:
                saved_image_url = download_image_to_library(image_url, product_id)
                if saved_image_url:
                    result["image_url"] = saved_image_url
                    result["image_saved_url"] = saved_image_url
                    result["image_success"] = True
                    result["image_reason"] = ""
                    image_fetched = True
                else:
                    result["image_reason"] = "failed to download image"
            else:
                result["image_reason"] = "no image found on source page"
        except Exception as exc:
            result["image_reason"] = f"source link unreachable: {str(exc)}"

    if not image_fetched:
        if not source_links_to_try:
            result["image_reason"] = "no source link available"
        # image_reason already set from last attempt

    # Overall success = both title and image succeeded
    result["success"] = result["title_success"] and result["image_success"]
    if not result["success"]:
        reasons = []
        if not result["title_success"]:
            reasons.append(f"title: {result['title_reason']}")
        if not result["image_success"]:
            reasons.append(f"image: {result['image_reason']}")
        result["reason"] = "; ".join(reasons)
    else:
        result["reason"] = ""

    return result


def _normalize_header(header: str) -> str:
    """Normalize header: lowercase, replace spaces/special chars with underscore, strip."""
    return re.sub(r'[\s\-]+', '_', header.strip().lower())


EXPECTED_HEADERS = [
    "Source link",
    "Competitor ASIN/link",
    "Product name",
    "Brand",
    "Cost",
    "Sell price",
    "Handling days",
    "Barcode",
]

REQUIRED_HEADERS = ["Source link", "Cost"]


def parse_csv_rows(raw: bytes) -> list[dict]:
    """Parse CSV or XLSX file and return list of dicts using exact header matching.
    Validates required columns upfront before processing any rows."""
    if not raw:
        raise ValueError("File is empty")

    # Try XLSX first if it looks like a binary file
    if raw[:2] == b'PK' or raw[:8] == b'PK\x03\x04':
        if not HAS_OPENPYXL:
            raise ValueError("XLSX files are not supported. Please use CSV format.")
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(raw))
            worksheet = workbook.active
            if not worksheet:
                raise ValueError("Excel file has no active sheet")

            # Read header row (exact, case-sensitive)
            raw_headers = []
            for cell in worksheet[1]:
                raw_headers.append(str(cell.value or "").strip())

            if not any(raw_headers):
                raise ValueError("Excel file has no header row")

            # Validate required columns exist
            missing_required = [h for h in REQUIRED_HEADERS if h not in raw_headers]
            if missing_required:
                raise ValueError(f"Missing required column(s): {', '.join(missing_required)}. Expected headers: {', '.join(EXPECTED_HEADERS)}")

            # Map expected headers to column indices
            header_to_idx = {h: raw_headers.index(h) for h in EXPECTED_HEADERS if h in raw_headers}

            # Read data rows
            rows = []
            for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                row_dict = {}
                for header, idx in header_to_idx.items():
                    val = row[idx] if idx < len(row) else ""
                    row_dict[header] = str(val or "").strip()
                # Only add if row has at least one non-empty value
                if any(row_dict.values()):
                    rows.append(row_dict)

            if not rows:
                raise ValueError("Excel file has no data rows (header only or all empty)")

            return rows
        except openpyxl.utils.exceptions.InvalidFileException:
            raise ValueError("Invalid Excel file format (.xlsx)")
        except Exception as exc:
            raise ValueError(f"Failed to parse Excel file: {str(exc)}")

    # Try CSV format
    try:
        text = raw.decode("utf-8-sig", errors="ignore")
        reader = csv.DictReader(io.StringIO(text))

        if not reader.fieldnames or not any(reader.fieldnames):
            raise ValueError("CSV file has no header row")

        raw_headers = list(reader.fieldnames)

        # Validate required columns exist
        missing_required = [h for h in REQUIRED_HEADERS if h not in raw_headers]
        if missing_required:
            raise ValueError(f"Missing required column(s): {', '.join(missing_required)}. Expected headers: {', '.join(EXPECTED_HEADERS)}")

        # Only keep expected headers that exist in the file
        available_headers = [h for h in EXPECTED_HEADERS if h in raw_headers]

        rows = []
        for row_num, row in enumerate(reader, start=2):
            row_dict = {}
            for header in available_headers:
                row_dict[header] = (str(row.get(header) or "").strip())
            if any(row_dict.values()):
                rows.append(row_dict)

        if not rows:
            raise ValueError("CSV file has no data rows (header only or all empty)")

        return rows
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Failed to parse CSV file: {str(exc)}")


app = FastAPI(title="Sellrix")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "amazon-app", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/register")
def register(payload: RegisterRequest):
    password_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()

    try:
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (payload.name, str(payload.email), password_hash),
            )
            conn.commit()
            user_id = cur.lastrowid
    except Exception as exc:
        if "UNIQUE constraint failed: users.email" in str(exc):
            raise HTTPException(status_code=409, detail="An account with that email already exists")
        raise HTTPException(status_code=500, detail="Unable to create account")

    return {
        "message": "Account created",
        "user": {"id": user_id, "name": payload.name, "email": str(payload.email)},
    }


@app.post("/api/login")
def login(payload: LoginRequest):
    password_hash = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (str(payload.email),),
        ).fetchone()

    if not user or user["password_hash"] != password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = jwt.encode(
        {
            "sub": str(user["id"]),
            "name": user["name"],
            "email": user["email"],
            "exp": datetime.utcnow() + timedelta(days=7),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return {
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
    }


@app.post("/api/logout")
def logout():
    return {"message": "Logged out"}


@app.get("/api/profile")
def profile(token: Optional[str] = None):
    # Frontend will send Authorization header in later phases. This placeholder
    # endpoint returns a lightweight demo profile for the dashboard shell.
    # The real token should be verified in the auth middleware in a production app.
    auth_token = token
    if not auth_token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        decoded = jwt.decode(auth_token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "id": int(decoded.get("sub")),
        "name": decoded.get("name"),
        "email": decoded.get("email"),
        "workspace": "Main Marketplace",
        "seller_account": "Seller Account #1",
    }


@app.post("/api/sourcing/products/fetch")
def fetch_product_from_source(payload: SourceProductRequest):
    """Fetch title + image from the active (cheapest in-stock) source link for a product, with a source-link fallback for manual adds."""
    source_link = payload.source_link or ""
    product_id = payload.product_id or payload.sku or hashlib.sha256(source_link.encode("utf-8")).hexdigest()[:12]

    if not source_link:
        # If a product id is passed, consult the repricer source list and choose the currently active source.
        product = next((p for p in REPRICER_PRODUCTS if p["id"] == product_id), None)
        if product:
            active_source = choose_active_source(product)
            if active_source:
                source_link = active_source.get("link") or ""

    if not source_link:
        raise HTTPException(status_code=400, detail="Missing source link")

    parsed = fetch_title_and_image_from_source_link(source_link, product_id)
    return {
        "title": parsed.get("title") or "",
        "image_url": parsed.get("image_saved_url") or parsed.get("image_url") or "",
        "success": parsed.get("success", False),
        "reason": parsed.get("reason") or "",
        "source": "active-source",
    }


# --- eBay Seller Bulk Fetch ---

EBAY_SELLER_FETCH_PROGRESS = {
    "running": False,
    "total": 0,
    "done": 0,
    "products": [],
    "skipped": [],
    "error": None,
}

COMPLIANCE_RISK_KEYWORDS = {
    "batteries": ["battery", "batteries", "lithium", "li-ion", "liion", "power bank", "rechargeable", "button cell"],
    "supplements_cosmetics": ["supplement", "vitamin", "cosmetic", "cream", "lotion", "serum", "skincare", "makeup", "lipstick", "foundation", "mascara", "eyeliner", "perfume", "fragrance", "essential oil", "protein powder", "dietary"],
    "children_toys": ["toy", "toys", "children", "kids", "baby", "infant", "toddler", "puzzle", "building block", "doll", "action figure", "stuffed", "plush", "rattle", "teether"],
    "electronics_certification": ["charger", "adapter", "cable", "cord", "power supply", "transformer", "inverter", "led light", "lamp", "bulb", "electronic", "circuit", "pcb", "arduino", "raspberry pi", "sensor", "module", "driver", "controller"],
    "weapons_knives": ["knife", "blade", "weapon", "tactical", "survival", "machete", "sword", "dagger", "pepper spray", "stun gun", "airsoft", "bb gun", "pellet", "crossbow", "bow"],
    "dangerous_goods": ["aerosol", "flammable", "corrosive", "toxic", "poison", "chemical", "solvent", "paint", "thinner", "acetone", "bleach", "propane", "butane", "lighter fluid"],
    "medical_devices": ["medical", "thermometer", "blood pressure", "glucose", "test strip", "lancet", "syringe", "needle", "bandage", "first aid", "hearing aid", "cpap", "nebulizer"],
    "branded_trademarked": ["nike", "adidas", "apple", "samsung", "sony", "louis vuitton", "gucci", "chanel", "rolex", "oakley", "ray-ban", "coach", "michael kors", "kate spade", "tiffany", "cartier", "pandora", "swarovski", "disney", "marvel", "star wars", "harry potter", "pokemon", "lego", "funko", "hot wheels", "barbie", "nerf", "hasbro", "mattel"],
}

def check_compliance_risk(product_title: str, product_category: str = "") -> dict:
    """Check if a product likely falls into a compliance-risk category."""
    text = (product_title + " " + product_category).lower()
    risks = []
    for category, keywords in COMPLIANCE_RISK_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                risks.append(category.replace("_", " ").title())
                break
    if risks:
        return {
            "flagged": True,
            "categories": risks,
            "reason": "Likely needs compliance approval: " + ", ".join(risks)
        }
    return {"flagged": False, "categories": [], "reason": ""}


def parse_ebay_seller_url(url: str) -> Optional[str]:
    """Extract seller username from eBay store/profile URL."""
    # eBay store URLs: https://www.ebay.com/str/SELLERNAME
    # eBay profile URLs: https://www.ebay.com/usr/SELLERNAME
    # Or just the username
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.strip("/")
    if path.startswith("str/"):
        return path[4:].split("/")[0]
    if path.startswith("usr/"):
        return path[4:].split("/")[0]
    if "." not in path and "/" not in path and len(path) > 0:
        return path
    return None


def fetch_ebay_seller_products(seller_username: str, max_products: int = 200) -> list:
    """Fetch all products from an eBay seller's store."""
    products = []
    page = 1
    
    while len(products) < max_products:
        # eBay store listing page
        url = f"https://www.ebay.com/str/{seller_username}/_pgn_{page}"
        try:
            html_text = fetch_page(url)
        except Exception as exc:
            if page == 1:
                raise HTTPException(status_code=400, detail=f"Could not access eBay seller store: {str(exc)}")
            break
        
        # Check if we hit the last page (no more products)
        if "No items match" in html_text or "no results" in html_text.lower() or "did not match" in html_text.lower():
            break
        
        # Extract product links from the listing page
        # eBay uses various patterns; try common ones
        item_links = re.findall(r'href="(https://www\.ebay\.com/itm/\d+)"', html_text)
        item_links += re.findall(r'href="(https://www\.ebay\.com/p/\d+)"', html_text)
        
        if not item_links:
            # Try alternative pattern for store listings
            item_links = re.findall(r'class="s-item__link" href="(https://www\.ebay\.com/itm/[^"]+)"', html_text)
            item_links += re.findall(r'data-view="mi:1686\|[^"]*" href="(https://www\.ebay\.com/itm/[^"]+)"', html_text)
        
        # Deduplicate
        item_links = list(dict.fromkeys(item_links))
        
        if not item_links:
            break
            
        for link in item_links:
            if len(products) >= max_products:
                break
            products.append({"source_link": link})
        
        page += 1
        if page > 50:  # Safety limit
            break
    
    return products


@app.post("/api/sourcing/ebay/fetch-seller")
async def fetch_ebay_seller(payload: dict):
    """Start fetching all products from an eBay seller's store."""
    seller_input = payload.get("seller_link", "") or payload.get("seller_username", "")
    if not seller_input:
        raise HTTPException(status_code=400, detail="Missing eBay seller link or username")
    
    seller_username = parse_ebay_seller_url(seller_input)
    if not seller_username:
        raise HTTPException(status_code=400, detail="Could not parse eBay seller from input. Provide a store link (ebay.com/str/NAME) or username.")
    
    # Reset progress
    EBAY_SELLER_FETCH_PROGRESS.update({
        "running": True,
        "total": 0,
        "done": 0,
        "products": [],
        "skipped": [],
        "error": None,
        "seller_username": seller_username,
    })
    
    def run_fetch():
        try:
            # Fetch product links from seller
            raw_products = fetch_ebay_seller_products(seller_username, max_products=200)
            EBAY_SELLER_FETCH_PROGRESS["total"] = len(raw_products)
            
            for idx, prod in enumerate(raw_products, start=1):
                try:
                    link = prod["source_link"]
                    product_id = hashlib.sha256(link.encode("utf-8")).hexdigest()[:12]
                    
                    # Fetch title and image
                    parsed = fetch_title_and_image_from_source_link(link, product_id)
                    title = parsed.get("title") or "Unknown"
                    image_url = parsed.get("image_saved_url") or parsed.get("image_url") or ""
                    
                    # Check compliance
                    compliance = check_compliance_risk(title, "")
                    
                    product_data = {
                        "source_link": link,
                        "title": title,
                        "image_url": image_url,
                        "compliance_flagged": compliance["flagged"],
                        "compliance_categories": compliance["categories"],
                        "compliance_reason": compliance["reason"],
                        "selected": not compliance["flagged"],  # Pre-select non-flagged
                    }
                    
                    if compliance["flagged"]:
                        EBAY_SELLER_FETCH_PROGRESS["skipped"].append(product_data)
                    else:
                        EBAY_SELLER_FETCH_PROGRESS["products"].append(product_data)
                    
                except Exception as exc:
                    EBAY_SELLER_FETCH_PROGRESS["skipped"].append({
                        "source_link": prod.get("source_link", ""),
                        "title": "Error fetching",
                        "image_url": "",
                        "compliance_flagged": True,
                        "compliance_categories": [],
                        "compliance_reason": f"Fetch error: {str(exc)}",
                        "selected": False,
                    })
                
                EBAY_SELLER_FETCH_PROGRESS["done"] = idx
            
            EBAY_SELLER_FETCH_PROGRESS["running"] = False
        except HTTPException as exc:
            EBAY_SELLER_FETCH_PROGRESS["running"] = False
            EBAY_SELLER_FETCH_PROGRESS["error"] = exc.detail
        except Exception as exc:
            EBAY_SELLER_FETCH_PROGRESS["running"] = False
            EBAY_SELLER_FETCH_PROGRESS["error"] = f"Unexpected error: {str(exc)}"
    
    thread = threading.Thread(target=run_fetch, daemon=True)
    thread.start()
    
    return {
        "status": "started",
        "seller_username": seller_username,
        "message": f"Started fetching products from eBay seller: {seller_username}",
    }


@app.get("/api/sourcing/ebay/fetch-progress")
def ebay_seller_fetch_progress():
    return EBAY_SELLER_FETCH_PROGRESS


@app.post("/api/sourcing/ebay/add-selected")
def add_ebay_selected(payload: dict):
    """Add selected products from eBay fetch to sourcing queue."""
    selected_products = payload.get("products", [])
    if not selected_products:
        raise HTTPException(status_code=400, detail="No products selected")
    
    added = []
    for prod in selected_products:
        if not prod.get("selected"):
            continue
        
        link = prod.get("source_link")
        if not link:
            continue
        
        product_id = hashlib.sha256(link.encode("utf-8")).hexdigest()[:12]
        parsed = fetch_title_and_image_from_source_link(link, product_id)
        
        # Add to sourcing queue (SOURCING_PRODUCTS)
        SOURCING_PRODUCTS.append({
            "id": product_id,
            "source_link": link,
            "competitor_link": "",
            "product_name": parsed.get("title") or prod.get("title") or "Unknown",
            "brand": "",
            "sku": product_id,
            "cost": 0,
            "sell_price": 0,
            "handling_days": "2-3 days",
            "barcode": "",
            "auto_price": "Suggested (auto-price)",
            "title_fetched": parsed.get("title") or "",
            "image_fetched": parsed.get("image_saved_url") or parsed.get("image_url") or "",
            "fetch_success": parsed.get("success", False),
            "fetch_reason": parsed.get("reason") or "",
        })
        
        added.append({
            "id": product_id,
            "title": parsed.get("title") or prod.get("title") or "Unknown",
            "source_link": link,
        })
    
    return {
        "added": len(added),
        "products": added,
        "message": f"Added {len(added)} products to sourcing queue"
    }


@app.get("/api/sourcing/import/template")
def download_import_template():
    """Download a blank Excel template with the exact required headers and empty rows."""
    from fastapi.responses import Response
    try:
        import openpyxl
        from openpyxl.styles import Font
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Import Template"
        
        # Write headers
        for col_idx, header in enumerate(EXPECTED_HEADERS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = Font(bold=True)
        
        # Add 10 empty rows for user to fill in
        for row_idx in range(2, 12):
            for col_idx in range(1, len(EXPECTED_HEADERS) + 1):
                ws.cell(row=row_idx, column=col_idx, value="")
        
        # Auto-fit column widths
        for col_idx, header in enumerate(EXPECTED_HEADERS, start=1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = max(len(header) + 2, 18)
        
        import io
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        xlsx_content = output.getvalue()
        
        return Response(
            content=xlsx_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=listinghub_import_template.xlsx"}
        )
    except ImportError:
        # Fallback to CSV if openpyxl not available
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(EXPECTED_HEADERS)
        # Add 10 empty rows
        for _ in range(10):
            writer.writerow([""] * len(EXPECTED_HEADERS))
        csv_content = output.getvalue()
        output.close()

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=listinghub_import_template.csv"}
        )


@app.get("/api/sourcing/import/progress")
def import_progress():
    return IMPORT_PROGRESS


@app.post("/api/sourcing/import")
async def import_products(file: UploadFile = File(...)):
    """Start a spreadsheet import job and return a mounted progress summary immediately, then let the UI poll the job via GET /api/sourcing/import/progress."""
    try:
        raw = await file.read()
        rows = parse_csv_rows(raw)
    except ValueError as exc:
        # Validation errors (empty file, no headers, wrong format, etc.)
        raise HTTPException(status_code=400, detail=f"File error: {str(exc)}") from exc
    except Exception as exc:
        # Unexpected errors
        raise HTTPException(status_code=400, detail=f"Unable to read spreadsheet file: {str(exc)}") from exc

    if not rows:
        raise HTTPException(status_code=400, detail="File has no data rows. Please provide a CSV or Excel file with at least one row of data (header + data).")

    job_id = hashlib.sha256(f"{datetime.utcnow().isoformat()}-{len(rows)}".encode()).hexdigest()[:16]

    IMPORT_PROGRESS.update({
        "job_id": job_id,
        "running": True,
        "total": len(rows),
        "done": 0,
        "success": 0,
        "failed": 0,
        "items": [],
    })

    def run_import():
        try:
            for idx, row in enumerate(rows, start=1):
                try:
                    # Use exact header names from EXPECTED_HEADERS
                    competitor_link = row.get("Competitor ASIN/link") or ""
                    source_link = row.get("Source link") or ""
                    product_name = row.get("Product name") or ""
                    brand = row.get("Brand") or ""
                    cost = row.get("Cost") or ""
                    sell_price = row.get("Sell price") or ""
                    handling_days = row.get("Handling days") or ""
                    barcode = row.get("Barcode") or ""

                    product_id = barcode or f"row-{idx}"

                    # Use the new function: title from competitor, image from active source
                    parse = fetch_title_from_competitor_image_from_active_source(
                        competitor_link=competitor_link,
                        product_id=product_id,
                        source_link=source_link
                    )

                    item = {
                        "row": idx,
                        "sku": product_id,
                        "product_name": product_name,
                        "brand": brand,
                        "cost": cost,
                        "sell_price": sell_price,
                        "handling_days": handling_days,
                        "barcode": barcode,
                        "title": parse.get("title") or "",
                        "image_url": parse.get("image_saved_url") or parse.get("image_url") or "",
                        "success": parse.get("success", False),
                        "reason": parse.get("reason") or "",
                        "title_success": parse.get("title_success", False),
                        "title_reason": parse.get("title_reason", ""),
                        "image_success": parse.get("image_success", False),
                        "image_reason": parse.get("image_reason", ""),
                    }

                    if parse.get("success"):
                        IMPORT_PROGRESS["success"] += 1
                        # Add successful products to the sourcing queue (Drafts)
                        SOURCING_PRODUCTS.append({
                            "id": product_id,
                            "source_link": source_link,
                            "competitor_link": competitor_link,
                            "product_name": parse.get("title") or product_name,
                            "brand": brand,
                            "sku": product_id,
                            "cost": float(cost) if cost else 0,
                            "sell_price": float(sell_price) if sell_price else 0,
                            "handling_days": handling_days or "2-3 days",
                            "barcode": barcode,
                            "auto_price": "Suggested (auto-price)",
                            "title_fetched": parse.get("title") or "",
                            "image_fetched": parse.get("image_saved_url") or parse.get("image_url") or "",
                            "fetch_success": True,
                            "fetch_reason": "",
                        })
                    else:
                        IMPORT_PROGRESS["failed"] += 1
                    IMPORT_PROGRESS["items"].append(item)
                except Exception as exc:
                    IMPORT_PROGRESS["failed"] += 1
                    IMPORT_PROGRESS["items"].append({
                        "row": idx,
                        "sku": row.get("Barcode") or f"row-{idx}",
                        "title": "",
                        "image_url": "",
                        "success": False,
                        "reason": f"link unreachable: {str(exc)}",
                    })

                IMPORT_PROGRESS["done"] = idx

            IMPORT_PROGRESS["running"] = False
        except Exception:
            IMPORT_PROGRESS["running"] = False
            IMPORT_PROGRESS["failed"] = max(IMPORT_PROGRESS.get("failed", 0), 1)

    thread = threading.Thread(target=run_import, daemon=True)
    thread.start()

    return {
        "status": "started",
        "job_id": job_id,
        "total": len(rows),
        "running": True,
        "message": "Bulk import started. Follow /api/sourcing/import/progress for rows 1..n."
    }


@app.post("/api/assistant/chat")
def chat_with_assistant(payload: ChatRequest):
    """Handle AI assistant chat requests with knowledge base and context awareness."""
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    user_message = payload.user_message or ""
    page_context = payload.page_context or ""
    
    # Read knowledge base
    try:
        kb_path = os.path.join(BASE_DIR, "ASSISTANT_KNOWLEDGE_BASE.md")
        with open(kb_path, "r", encoding="utf-8") as f:
            knowledge_base = f.read()
    except Exception:
        knowledge_base = "Knowledge base unavailable."
    
    # Build conversation history for context
    messages_for_api = []
    for msg in payload.messages:
        messages_for_api.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Detect language from user message
    def detect_language(text: str) -> str:
        """Detect the primary language of the text."""
        # Urdu/Hindi (Devanagari or Arabic script)
        if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
            return "urdu"
        if re.search(r'[\u0900-\u097F]', text):  # Devanagari (Hindi)
            return "hindi"
        # Chinese
        if re.search(r'[\u4e00-\u9fff]', text):
            return "chinese"
        # Japanese
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text):
            return "japanese"
        # Korean
        if re.search(r'[\uAC00-\uD7AF]', text):
            return "korean"
        # Arabic
        if re.search(r'[\u0600-\u06FF]', text):
            return "arabic"
        # Spanish
        if re.search(r'\b(como|cómo|qué|que|dónde|donde|cuándo|cuando|por qué|porque|gracias|hola|ayuda|ayúdame)\b', text.lower()):
            return "spanish"
        # French
        if re.search(r'\b(comment|quoi|où|quand|pourquoi|merci|bonjour|aide|aidez-moi)\b', text.lower()):
            return "french"
        # German
        if re.search(r'\b(wie|was|wo|wann|warum|danke|hallo|hilfe|helfen)\b', text.lower()):
            return "german"
        # Portuguese
        if re.search(r'\b(comio|como|o quê|que|onde|quando|por que|obrigado|olá|ajuda|ajude-me)\b', text.lower()):
            return "portuguese"
        # Default to English
        return "english"
    
    user_language = detect_language(user_message)
    
    # Simple translation for mock fallback (Urdu/Hindi in Roman script)
    def translate_to_urdu(text: str) -> str:
        """Translate common English phrases to Roman Urdu for mock responses."""
        translations = {
            "This is the **Add New Product** page. You have three ways to add products:\n\n1. **Add One Product** — Paste a product link (from supplier, eBay, AliExpress, etc.) and we'll fetch the title and image automatically. Fill in your cost and sell price, then click \"Fetch details & add to queue\".\n\n2. **Import from Spreadsheet** — Download the template, fill in your product data (source link, cost, etc.), upload the CSV/Excel file, and we'll process all rows at once.\n\n3. **Fetch from eBay Seller** — Enter an eBay store link or username. We'll pull all their listings, auto-skip compliance-risk items, and let you choose which to add to your queue.\n\n**Important**: The source link is required — we use it to get the product's title and photo automatically. Your product queue on the right shows everything you've added but not yet submitted to Amazon.": 
                "یہ **Add New Product** کا صفحہ ہے۔ آپ کے پاس تین طریقے ہیں Products شامل کرنے کے:\n\n1. **Add One Product** — Product کا link پیسٹ کریں (supplier، eBay، AliExpress وغیرہ سے) اور ہم title اور image خود fetch کر لیں گے۔ اپنا cost اور sell price بھر کے \"Fetch details & add to queue\" کلک کریں۔\n\n2. **Import from Spreadsheet** — Template download کریں، اپنا data بھریں (source link، cost، وغیرہ)، CSV/Excel file upload کریں، اور ہم سارے rows ایک ساتھ process کر لیں گے۔\n\n3. **Fetch from eBay Seller** — eBay store کا link یا username درج کریں۔ ہم ان کی تمام listings kéo لیں گے، compliance-risk items کو skip کر دیں گے، اور آپ کو منتخب کرنے دیں گے کہ کون سے queue میں شامل کریں۔\n\n**اہم**: Source link درکار ہے — ہم اس کا استعمال کرتے ہیں product کا title اور photo خود حاصل کرنے کے لیے۔ آپ کا product queue دائیں طرف دکھائی دیتا ہے جوproducts آپ نے شامل کیے ہیں لیکن ابھی تک Amazon پر submit نہیں کیے۔",
            
            "This is the **Add New Product** page. You have three ways to add products to your queue:\n- **Add One Product**: Paste a link, we fetch title/image, you fill in pricing\n- **Import from Spreadsheet**: Upload a CSV/Excel file with many products\n- **Fetch from eBay Seller**: Enter a seller's store link, we pull all their listings\n\nYour product queue on the right shows everything added but not yet submitted to Amazon. Click any item to review details.":
                "یہ **Add New Product** کا صفحہ ہے۔ آپ کے پاس تین طریقے ہیں products queue میں شامل کرنے کے:\n- **Add One Product**: Link پیسٹ کریں، ہم title/image fetch کرتے ہیں، آپ pricing بھریں\n- **Import from Spreadsheet**: CSV/Excel file upload کریں بہت سारे products کے ساتھ\n- **Fetch from eBay Seller**: Seller کا store link درج کریں، ہم ان کی تمام listings kéo لیں گے\n\nآپ کا product queue دائیں طرف دکھتا ہے جو products شامل کیے گئے ہیں لیکن ابھی Amazon پر submit نہیں ہوئے۔ کوئی بھی item کلک کریں details دیکھنے کے لیے۔",
            
            "**Fetch from eBay Seller** lets you pull all products from one eBay seller's store:\n- Paste their store link (like `https://www.ebay.com/str/storename`) or just their username\n- Click \"Fetch all products\" — we'll scan their store page by page\n- We auto-skip items with compliance risks (batteries, supplements, toys, etc.)\n- You review the results, check/uncheck products, then click \"Add selected to queue\"\n- Added products appear in your product queue on the right\n\nThe source link for each product will be the eBay listing URL.":
                "**Fetch from eBay Seller** آپ کو اجازت دیتا ہے کہ ایک eBay seller کی store سے تمام products کھینچ لیں:\n- ان کا store link پیسٹ کریں (جیسے `https://www.ebay.com/str/storename`) یا بس ان کا username\n- \"Fetch all products\" کلک کریں — ہم ان کی store کو page by page scan کریں گے\n- ہم خود compliance risks والے items skip کر دیں گے (batteries، supplements، toys، وغیرہ)\n- آپ results review کریں، products check/uncheck کریں، پھر \"Add selected to queue\" کلک کریں\n- شامل کیے گئے products آپ کے product queue میں دائیں طرف دکھائی دیں گے\n\nهر product کا source link eBay listing URL ہوگا۔",
            
            "**Import from Spreadsheet** adds many products at once:\n1. Click \"Download template\" to get the exact column format\n2. Fill in: Source link (required), Competitor ASIN/link, Product name, Brand, Cost (required), Sell price, Handling days, Barcode\n3. Save as CSV or Excel (.xlsx)\n4. Choose the file and click \"Import rows\"\n5. We process each row, fetch titles/images from links, and add successful ones to your queue\n\nRequired columns: **Source link** and **Cost**. The template has all columns pre-labeled.":
                "**Import from Spreadsheet** ایک ساتھ بہت سारे products شامل کرتا ہے:\n1. \"Download template\" کلک کریں exact column format حاصل کرنے کے لیے\n2. بھریں: Source link (درکار)، Competitor ASIN/link، Product name، Brand، Cost (درکار)، Sell price، Handling days، Barcode\n3. CSV یا Excel (.xlsx) کے طور پر save کریں\n4. File چنیں اور \"Import rows\" کلک کریں\n5. ہم ہر row process کرتے ہیں، links سے titles/images fetch کرتے ہیں، اور کامیاب rows کو آپ کی queue میں شامل کرتے ہیں\n\nدرکار کالم: **Source link** اور **Cost**۔ Template میں تمام columns pre-labeled ہیں۔",
            
            "This is the **Listing Detail** page. Review and complete all product details before submitting to Amazon:\n- **Product Details tab**: Title, brand, condition, bullets, description, backend keywords\n- **Images tab**: Manage product images (Main, lifestyle, A+ modules)\n- **Offer & Pricing tab**: Your cost, sell price, handling time, barcode, pricing method\n- **Safety & Compliance tab**: Compliance checks (restricted categories, claim risk, required documents)\n\nUse **Auto-fix** to auto-populate from source link and AI, **Generate AI content** for listing text, and **Open Image Studio** for images. When everything looks good, click **Submit to Amazon**.":
                "یہ **Listing Detail** کا صفحہ ہے۔ Amazon پر submit کرنے سے پہلے تمام product details review اور complete کریں:\n- **Product Details tab**: Title، brand، condition، bullets، description، backend keywords\n- **Images tab**: Product images میںجاز کریں (Main، lifestyle، A+ modules)\n- **Offer & Pricing tab**: آپ کا cost، sell price، handling time، barcode، pricing method\n- **Safety & Compliance tab**: Compliance checks (restricted categories، claim risk، required documents)\n\n**Auto-fix** استعمال کریں source link اور AI سے auto-populate کرنے کے لیے، **Generate AI content** listing text کے لیے، اور **Open Image Studio** images کے لیے۔ جب سب چیز اچھی لگی تو **Submit to Amazon** کلک کریں۔",
            
            "**Auto-fill missing fields** (the \"Auto-fix\" button) automatically populates empty fields:\n- It fetches data from your source link (title, brand, category, description, bullets)\n- It uses AI to generate missing content (bullets, description, keywords)\n- It shows a preview with 3 columns: ✓ Filled from source, 🤖 Filled by AI (review carefully), ⚠ Still needs your attention\n- You review each item, then click \"Submit to Amazon\" when ready\n\nAlways review AI-generated content before submitting — it may need corrections.":
                "**Auto-fill missing fields** (\"Auto-fix\" بٹن) خالی fields کو خود پورا کرتا ہے:\n- یہ آپ کے source link سے data fetch کرتا ہے (title، brand، category، description، bullets)\n- یہ AI استعمال کرتا ہے missing content generate کرنے کے لیے (bullets، description، keywords)\n- یہ preview دکھاتا ہے 3 columns کے ساتھ: ✓ Source سے بھرا، 🤖 AI سے بھرا (احتیاط سے review کریں)، ⚠ ابھی آپ کی توجہ درکار ہے\n- آپہر item review کریں، پھر \"Submit to Amazon\" کلک کریں جب تیار ہوں\n\nہamesha AI-generated content review کریں submit کرنے سے پہلے — اس میں ترمیم کی ضرورت ہو سکتی ہے۔",
            
            "**Generate AI Content** creates listing text using AI:\n- Click \"Generate AI content\" button\n- It creates: Title (max 200 chars), 5 Bullet points, Full description (HTML allowed), Backend keywords (comma-separated, max 250 bytes)\n- The generated content appears in the AI Content panel — you can edit it before saving\n- Click \"Save AI content to this listing\" to apply it\n\nMake sure your product name and brand are filled in first for best results.":
                "**Generate AI Content** AI استعمال کر کے listing text بناتا ہے:\n- \"Generate AI content\" بٹن کلک کریں\n- یہ بناتا ہے: Title (مکسیمم 200 characters)، 5 Bullet points، پورا description (HTML allowed)، Backend keywords (comma-separated، مکسیمم 250 bytes)\n- Generated content AI Content panel میں دکھائی دیتا ہے — آپ اسے save کرنے سے پہلے edit کر سکتے ہیں\n- \"Save AI content to this listing\" کلک کریں apply کرنے کے لیے\n\nیقینی بنائیں کہ آپ کا product name اور brand پہلے سے bhare hue ہوں بہترین نتائج کے لیے۔",
            
            "**Images** on this page:\n- The main product image shows in the sidebar (fetched from your source link)\n- Click \"Open Image Studio\" to create new AI-generated images\n- In the Images tab, you can assign images to slots: Main (white background), Image 1-4, A+ modules\n- Amazon requires the Main image on pure white background\n\nUse Image Studio for lifestyle shots, infographics, or A+ content modules.":
                "**Images** اس صفحے پر:\n- Main product image sidebar میں دکھتا ہے (آپ کے source link سے fetch ہوا)\n- \"Open Image Studio\" کلک کریں نئی AI-generated images بنانے کے لیے\n- Images tab میں، آپ images slots کو assign کر سکتے ہیں: Main (white background)، Image 1-4، A+ modules\n- Amazon Main image پر pure white background کا مطالبہ کرتا ہے\n\nImage Studio استعمال کریں lifestyle shots، infographics، یا A+ content modules کے لیے۔",
            
            "This is the **All Listings** page. View and manage every product listing:\n- **Tabs**: All listings / Drafts (not submitted) / Live on Amazon\n- Each row shows: image, title, ASIN/SKU/barcode, brand, condition, handling time, cost, Amazon fees, estimated profit, status\n- Status badges: Draft (not submitted), Live on Amazon, Needs your review, Amazon rejected\n- Click \"Add new product\" to go to the Sourcing page\n- Use \"Filter listings\" to narrow down by status, category, etc.\n\nDrafts are products in your queue not yet sent to Amazon. Live listings are already published.":
                "یہ **All Listings** کا صفحہ ہے۔ ہر product listing کو دیکھیں اورmanage کریں:\n- **Tabs**: All listings / Drafts (submit نہیں ہوئے) / Live on Amazon\n- ہر row دکھاتا ہے: image، title، ASIN/SKU/barcode، brand، condition، handling time، cost، Amazon fees، estimated profit، status\n- Status badges: Draft (submit نہیں ہوئے)، Live on Amazon، آپ کی review درکار، Amazon rejected\n- \"Add new product\" کلک کریں Sourcing page جانے کے لیے\n- \"Filter listings\" استعمال کریں status، category، وغیرہ کے لحاظ سے narrow down کرنے کے لیے\n\nDrafts وہ products ہیں جو آپ کی queue میں ہیں لیکن ابھی Amazon نہیں بھیجے گئے۔ Live listings پہلے سے published ہیں۔",
            
            "This is the **Dashboard** — your Amazon business at a glance:\n- **KPIs**: Monthly revenue, active listings, profit margin, items needing attention\n- **Products in progress**: Draft listings being worked on (not live yet)\n- **Account health**: Listing quality, Amazon sync, content quality scores (green=good, orange=needs work, red=urgent)\n\nUse the sidebar to navigate to Sourcing (add products), Listings (manage all), or other tools.":
                "یہ **Dashboard** ہے — آپ کا Amazon business ایک نظر میں:\n- **KPIs**: Monthly revenue، active listings، profit margin، items جو توجہ چاہتے ہیں\n- **Products in progress**: Draft listings پر کام چل رہا ہے (ابھی live نہیں)\n- **Account health**: Listing quality، Amazon sync، content quality scores (green=اچھا، orange=کام چاہیے، red=فوری)\n\nSidebar استعمال کریں navigate کرنے کے لیے Sourcing (products شامل کریں)، Listings (سب manage کریں)، یا دیگر tools تک۔",
            
            "This is **Catalog Analytics** — see what drives your business:\n- **Revenue concentration**: % of revenue from top 5 products (high = consider diversifying)\n- **Best performer**: Your highest-revenue product\n- **Dead stock**: Products with zero sales for 90+ days (consider repricing or removing)\n- **Product performance table**: Ranked by revenue with units sold, profit, ROI, and status\n\nROI = profit ÷ cost. Higher is better. Filter by time period using the dropdown.":
                "یہ **Catalog Analytics** ہے — دیکھیں کیا آپ کے business کو drive کرتا ہے:\n- **Revenue concentration**: % revenue top 5 products سے (high = diversify کرنے کا خیال کریں)\n- **Best performer**: آپ کا سب سے زیادہ revenue والا product\n- **Dead stock**: Products जिनہیں 90+ دن سے sales نہیں ملی (repricing یا remove کرنے کا خیال کریں)\n- **Product performance table**: Revenue کی بنیاد پر ranked ساتھ units sold، profit، ROI، اور status\n\nROI = profit ÷ cost۔ زiyada بہتر ہے۔ Dropdown استعمال کریں time period filter کرنے کے لیے۔",
            
            "This is the **Category Explorer** — find the right Amazon category:\n- Browse the Amazon category tree (click to expand)\n- Each category shows selling requirements, fees, and required product attributes\n- Your listings by category shows how many active listings you have in each top-level category\n\nThe correct category affects fees, visibility, and what info Amazon requires. Click \"Browse full category tree\" for more.":
                "یہ **Category Explorer** ہے — صحیح Amazon category تلاش کریں:\n- Amazon category tree browse کریں (expand کرنے کے لیے کلک کریں)\n- ہر category دکھاتی ہے selling requirements، fees، اور required product attributes\n- آپ کی listings by category دکھاتی ہے کہ آپ کے کتنے active listings ہیں ہر top-level category میں\n\nصحیح category fees، visibility، اور جو info Amazon چاہتا ہے اس پر اثر ڈالتا ہے۔ \"Browse full category tree\" کلک کریں مزید کے لیے۔",
            
            "This is the **Variations** page — group related products under one Amazon listing:\n- Each group = one parent listing with multiple child options (size, color, style)\n- Customers see all options on a single product page\n- Click \"Create variation set\" to start a new group\n- Status shows if synced on Amazon or needs review\n\nVariations let customers pick their option without leaving the page.":
                "یہ **Variations** کا صفحہ ہے — متعلقہ products کو ایک Amazon listing کے تحت گروپ کریں:\n- ہر group = ایک parent listing múltiples child options کے ساتھ (size، color، style)\n- Customers تمام options دیکھتے ہیں ایک ہی product page پر\n- \"Create variation set\" کلک کریں نئی group شروع کرنے کے لیے\n- Status دکھاتا ہے کہ Amazon پر synced ہے یا review درکار ہے\n\nVariations customers کو اجازت دیتا ہیں کہ وہ بغیر page چھوڑے اپنا option چنیں۔",
            
            "This is the **AI Image Studio** — create product images with AI:\n- **Preview panel**: Shows generated image, fidelity slider (higher = closer to real product), standing instructions\n- **Tabs**: Creative concepts / Main image (white bg) / Secondary images / A+ Content modules\n- Settings: How close to real product, image slot, secondary approach (AI suggest vs manual), template\n- Click \"Generate image\" then \"Assign to listing slot\" to add to your product\n\nMain images MUST be on pure white background per Amazon rules.":
                "یہ **AI Image Studio** ہے — AI کے ساتھ product images بنائیں:\n- **Preview panel**: Generated image دکھاتا ہے، fidelity slider (زائدہ = واقعی product کے قریب)، standing instructions\n- **Tabs**: Creative concepts / Main image (white bg) / Secondary images / A+ Content modules\n- Settings: واقعی product سے کتنا قریب، image slot، secondary approach (AI suggest vs manual)، template\n- \"Generate image\" کلک کریں پھر \"Assign to listing slot\" اپنے product میں شامل کرنے کے لیے\n\nMain images ضروری ہیں pure white background پر Amazon rules کے مطابق۔",
            
            "This is the **Image Library** — all your generated and uploaded images:\n- Filter by listing, image slot (Main, Image 1-4, A+), or status (Active, Draft, Queued)\n- Active = assigned to a live listing, Draft = saved but not assigned, Queued = processing\n- Click \"Create new images\" to go to Image Studio\n- \"Upload image set\" and \"Download as ZIP\" for bulk operations":
                "یہ **Image Library** ہے — آپ کی تمام generated اور uploaded images:\n- Filter کریں listing، image slot (Main، Image 1-4، A+)، یا status (Active، Draft، Queued) کی بنیاد پر\n- Active = live listing کو assign، Draft = save ہوا لیکن assign نہیں، Queued = process ہو رہا ہے\n- \"Create new images\" کلک کریں Image Studio جانے کے لیے\n- \"Upload image set\" اور \"Download as ZIP\" bulk operations کے لیے",
            
            "This is **Image References** — save reference images to guide AI generation:\n- Add images from suppliers, competitors, or brand guidelines\n- They tell the AI what style, angle, and composition you want\n- Set visual style (clean white, lifestyle, infographic), brand colors, and notes for AI\n- \"Generate test image\" to preview the style\n\nReferences help AI match your brand's visual identity.":
                "یہ **Image References** ہے — reference images save کریں AI generation کی رہنمائی کے لیے:\n- Images شامل کریں suppliers، competitors، یا brand guidelines سے\n- یہ AI کو بتاتے ہیں کہ آپ کو کونسا style، angle، اور composition چاہیے\n- Visual style set کریں (clean white، lifestyle، infographic)، brand colors، اور AI کے لیے notes\n- \"Generate test image\" style preview کرنے کے لیے\n\nReferences AI کو مدد کرتے ہیں آپ کی brand کی visual identity match کرنے میں۔",
            
            "This is the **Repricer** — automatically adjust Amazon prices when supplier costs change:\n- **Profit rule** (applies to all products): Percentage (e.g., \"keep 20% margin\") or Fixed amount (e.g., \"$5 profit\")\n- System watches your supplier links, finds the cheapest **in-stock** source, sets your Amazon price to maintain margin\n- Each product shows: current Amazon price, cheapest in-stock supplier, status (Auto-priced / No source available)\n- Click \"Check supplier prices now\" to refresh, \"Save profit rule\" to update\n\nOnly in-stock sources are considered — out-of-stock competitors are ignored.":
                "یہ **Repricer** ہے — Amazon prices کو خود adjust کرتا ہے جب supplier costs بدلتے ہیں:\n- **Profit rule** (سب products پر لاگو): Percentage (مثال: \"20% margin رکھیں\") یا Fixed amount (مثال: \"$5 profit\")\n- System آپ کے supplier links کو دیکھتا ہے، سب سے سستا **in-stock** source تلاش کرتا ہے، آپ کی Amazon price set کرتا ہے margin برقرار رکھنے کے لیے\n- ہر product دکھاتا ہے: موجودہ Amazon price، سب سے سستا in-stock supplier، status (Auto-priced / No source available)\n- \"Check supplier prices now\" کلک کریں refresh کرنے کے لیے، \"Save profit rule\" update کرنے کے لیے\n\nصرف in-stock sources considérés جاتے ہیں — out-of-stock competitors ignore کئے جاتے ہیں۔",
            
            "Amazon has comprehensive policies for sellers. Key areas:\n\n**Fees**: Referral fees (8-15% by category), $39.99/month for professional sellers, FBA fulfillment fees.\n\n**Listing Requirements**: Accurate info, at least one image, proper category, content guidelines compliance.\n\n**Account Health**: Cancellation rate, defect rate, late shipment rate — Amazon restricts selling if these fall below standards.\n\n**Common Issues**: Pricing errors trigger suppression, keyword stuffing violates guidelines, cross-shipping between marketplaces not allowed.\n\nFor specific policy questions, check Amazon Seller Central's Policy section or contact Seller Support, as policies change.":
                "Amazon کے sellers کے لیے جامع policies ہیں۔ اہم علاقے:\n\n**Fees**: Referral fees (8-15% category کے لحاظ سے)، $39.99/month professional sellers کے لیے، FBA fulfillment fees۔\n\n**Listing Requirements**: درست معلومات، کم از کم ایک image، مناسب category، content guidelines compliance۔\n\n**Account Health**: Cancellation rate، defect rate، late shipment rate — Amazon selling restrict کر دیتا ہے اگر یہ standards سے نیچے گرجائیں۔\n\n**Common Issues**: Pricing errors suppression trigger کرتے ہیں، keyword stuffing guidelines violate کرتا ہے، cross-shipping marketplaces کے درمیان allowed نہیں۔\n\nمخصوص policy سوالات کے لیے، Amazon Seller Central کا Policy section چیک کریں یا Seller Support سے رابطہ کریں، کیونکہ policies بدلتی رہتی ہیں۔",
            
            "**Pricing & Repricing in Sellrix:**\n\n**Profit Calculation**: \n- Profit = Sell Price - Cost\n- Profit Margin % = (Profit / Sell Price) × 100\n\n**Repricing Feature**:\n- System checks all your supplier/competitor sources\n- Picks the cheapest one that's \"In Stock\"\n- Calculates minimum price to maintain your profit margin\n- Set profit as percentage (20%) or fixed amount ($5)\n\n**Example**: Cheapest supplier $10, 20% profit → recommended price $12.\n\nOut-of-stock sources are ignored. Configure your rule on the Repricer page.":
                "**Pricing & Repricing in Sellrix:**\n\n**Profit Calculation**: \n- Profit = Sell Price - Cost\n- Profit Margin % = (Profit / Sell Price) × 100\n\n**Repricing Feature**:\n- System آپ کے تمام supplier/competitor sources چیک کرتا ہے\n- سب سے سستا اٹھاتا ہے جو \"In Stock\" ہو\n- Minimum price calculate کرتا ہے آپ کا profit margin برقرار رکھنے کے لیے\n- Profit set کریں percentage (20%) یا fixed amount ($5) کے طور پر\n\n**مثال**: سب سے سستا supplier $10، 20% profit → تجویز کردہ price $12۔\n\nOut-of-stock sources ignore کئے جاتے ہیں۔ اپنا rule Repricer page پر configure کریں۔",
            
            "I'm your Sellrix AI assistant. I can help with:\n\n1. **This page** — Ask \"What is this page for?\" or \"How do I...?\"\n2. **Amazon policies** — Fees, requirements, account health\n3. **Your listings** — Data, status, improvements\n4. **Pricing/Repricing** — Profit calculations, margin rules\n\nWhat would you like to know? I'll answer in the same language you asked.":
                "میں آپ کا Sellrix AI assistant ہوں۔ میں مدد کر سکتا ہوں:\n\n1. **یہ صفحہ** — پوچھیں \"یہ صفحہ کس لیے ہے؟\" یا \"میں کیسے...؟\"\n2. **Amazon policies** — Fees، requirements، account health\n3. **آپ کی listings** — Data، status، improvements\n4. **Pricing/Repricing** — Profit calculations، margin rules\n\nآپ کیا جاننا چاہتے ہیں؟ میں آپ کی زبان میں جواب دوں گا۔",
        }
        return translations.get(text, text)
    
    def translate_to_hindi(text: str) -> str:
        """Translate common English phrases to Roman Hindi for mock responses."""
        # For now, use Urdu translations as they're very similar in Roman script
        return translate_to_urdu(text)
    
    # Language-specific instructions for the AI
    language_instructions = {
        "english": "Reply in English.",
        "urdu": "Reply in Urdu (Roman Urdu is fine).",
        "hindi": "Reply in Hindi (Roman Hindi/Hinglish is fine).",
        "chinese": "Reply in Simplified Chinese.",
        "japanese": "Reply in Japanese.",
        "korean": "Reply in Korean.",
        "arabic": "Reply in Arabic.",
        "spanish": "Reply in Spanish.",
        "french": "Reply in French.",
        "german": "Reply in German.",
        "portuguese": "Reply in Portuguese.",
    }
    
    language_instruction = language_instructions.get(user_language, "Reply in English.")
    
    # System prompt with knowledge base and context
    system_prompt = f"""You are a helpful AI assistant for Sellrix, a seller operations tool for Amazon sellers.

## Your Knowledge Sources:

### 1. App-Specific Knowledge (Primary Authority)
{knowledge_base}

### 2. Amazon Seller Central Knowledge
You also know about:
- Amazon's seller policies, fees, and requirements
- How to manage product listings on Amazon
- Amazon's categories, compliance rules, and account health
- Common Amazon error codes and their meanings
- Best practices for Amazon selling

### 3. Context About User's Current Activity
{page_context}

## Important Guidelines:
1. **Accuracy First**: If the user asks about a specific feature in THIS app, refer to the app knowledge base. If it's about Amazon policy, use your general knowledge but acknowledge if something might have changed.
2. **Honesty**: If you're not certain about something (especially Amazon policies that may have changed), say so clearly instead of guessing.
3. **Clarity**: Explain things in plain language, not jargon. If you use technical terms, explain them.
4. **Context-Aware**: Use the user's current page context to give more relevant answers. Focus on what they can do on THIS specific page.
5. **Helpful**: Provide step-by-step guidance when explaining how to do something in the app or on Amazon.
6. **Language**: {language_instruction} Always respond in the same language the user wrote in.

Now help the user with their question."""
    
    # Pre-translated responses for mock fallback (Urdu/Hindi in Roman script)
    urdu_responses = {
        "add_new_product_general": """یہ **Add New Product** کا صفحہ ہے۔ آپ کے پاس تین طریقے ہیں products شامل کرنے کے:
- **Add One Product**: Link پیسٹ کریں، ہم title/image fetch کرتے ہیں، آپ pricing بھریں
- **Import from Spreadsheet**: CSV/Excel file upload کریں بہت سारे products کے ساتھ
- **Fetch from eBay Seller**: Seller کا store link درج کریں، ہم ان کی تمام listings kéo لیں گے

آپ کا product queue دائیں طرف دکھتا ہے جو products شامل کیے گئے ہیں لیکن ابھی Amazon پر submit نہیں ہوئے۔ کوئی بھی item کلک کریں details دیکھنے کے لیے۔""",
        
        "add_new_product_detailed": """یہ **Add New Product** کا صفحہ ہے۔ آپ کے پاس تین طریقے ہیں Products شامل کرنے کے:

1. **Add One Product** — Product کا link پیسٹ کریں (supplier، eBay، AliExpress وغیرہ سے) اور ہم title اور image خود fetch کر لیں گے۔ اپنا cost اور sell price بھر کے "Fetch details & add to queue" کلک کریں۔

2. **Import from Spreadsheet** — Template download کریں، اپنا data بھریں (source link، cost، وغیرہ)، CSV/Excel file upload کریں، اور ہم سارے rows ایک ساتھ process کر لیں گے۔

3. **Fetch from eBay Seller** — eBay store کا link یا username درج کریں۔ ہم ان کی تمام listings kéo لیں گے، compliance-risk items کو skip کر دیں گے، اور آپ کو منتخب کرنے دیں گے کہ کون سے queue میں شامل کریں۔

**اہم**: Source link درکار ہے — ہم اس کا استعمال کرتے ہیں product کا title اور photo خود حاصل کرنے کے لیے۔ آپ کا product queue دائیں طرف دکھائی دیتا ہے جو products آپ نے شامل کیے ہیں لیکن ابھی تک Amazon پر submit نہیں کیے۔""",
        
        "ebay_fetch": """**Fetch from eBay Seller** آپ کو اجازت دیتا ہے کہ ایک eBay seller کی store سے تمام products کھینچ لیں:
- ان کا store link پیسٹ کریں (جیسے `https://www.ebay.com/str/storename`) یا بس ان کا username
- "Fetch all products" کلک کریں — ہم ان کی store کو page by page scan کریں گے
- ہم خود compliance risks والے items skip کر دیں گے (batteries، supplements، toys، وغیرہ)
- آپ results review کریں، products check/uncheck کریں، پھر "Add selected to queue" کلک کریں
- شامل کیے گئے products آپ کے product queue میں دائیں طرف دکھائی دیں گے

ہر product کا source link eBay listing URL ہوگا۔""",
        
        "import_spreadsheet": """**Import from Spreadsheet** ایک ساتھ بہت سारे products شامل کرتا ہے:
1. "Download template" کلک کریں exact column format حاصل کرنے کے لیے
2. بھریں: Source link (درکار)، Competitor ASIN/link، Product name، Brand، Cost (درکار)، Sell price، Handling days، Barcode
3. CSV یا Excel (.xlsx) کے طور پر save کریں
4. File چنیں اور "Import rows" کلک کریں
5. ہم ہر row process کرتے ہیں، links سے titles/images fetch کرتے ہیں، اور کامیاب rows کو آپ کی queue میں شامل کرتے ہیں

درکار کالم: **Source link** اور **Cost**۔ Template میں تمام columns pre-labeled ہیں۔""",
        
        "listing_detail_general": """یہ **Listing Detail** کا صفحہ ہے۔ Amazon پر submit کرنے سے پہلے تمام product details review اور complete کریں:
- **Product Details tab**: Title، brand، condition، bullets، description، backend keywords
- **Images tab**: Product images میںجاز کریں (Main، lifestyle، A+ modules)
- **Offer & Pricing tab**: آپ کا cost، sell price، handling time، barcode، pricing method
- **Safety & Compliance tab**: Compliance checks (restricted categories، claim risk، required documents)

**Auto-fix** استعمال کریں source link اور AI سے auto-populate کرنے کے لیے، **Generate AI content** listing text کے لیے، اور **Open Image Studio** images کے لیے۔ جب سب چیز اچھی لگی تو **Submit to Amazon** کلک کریں۔""",
        
        "auto_fix": """**Auto-fill missing fields** (\"Auto-fix\" بٹن) خالی fields کو خود پورا کرتا ہے:
- یہ آپ کے source link سے data fetch کرتا ہے (title، brand، category، description، bullets)
- یہ AI استعمال کرتا ہے missing content generate کرنے کے لیے (bullets، description، keywords)
- یہ preview دکھاتا ہے 3 columns کے ساتھ: ✓ Source سے بھرا، 🤖 AI سے بھرا (احتیاط سے review کریں)، ⚠ ابھی آپ کی توجہ درکار ہے
- آپ ہر item review کریں، پھر "Submit to Amazon" کلک کریں جب تیار ہوں

ہمیشہ AI-generated content review کریں submit کرنے سے پہلے — اس میں ترمیم کی ضرورت ہو سکتی ہے۔""",
        
        "ai_content": """**Generate AI Content** AI استعمال کر کے listing text بناتا ہے:
- "Generate AI content" بٹن کلک کریں
- یہ بناتا ہے: Title (مکسیمم 200 characters)، 5 Bullet points، پورا description (HTML allowed)، Backend keywords (comma-separated، مکسیمم 250 bytes)
- Generated content AI Content panel میں دکھائی دیتا ہے — آپ اسے save کرنے سے پہلے edit کر سکتے ہیں
- "Save AI content to this listing" کلک کریں apply کرنے کے لیے

یقینی بنائیں کہ آپ کا product name اور brand پہلے سے bhare hue ہوں بہترین نتائج کے لیے۔""",
        
        "images": """**Images** اس صفحے پر:
- Main product image sidebar میں دکھتا ہے (آپ کے source link سے fetch ہوا)
- "Open Image Studio" کلک کریں نئی AI-generated images بنانے کے لیے
- Images tab میں، آپ images slots کو assign کر سکتے ہیں: Main (white background)، Image 1-4، A+ modules
- Amazon Main image پر pure white background کا مطالبہ کرتا ہے

Image Studio استعمال کریں lifestyle shots، infographics، یا A+ content modules کے لیے۔""",
        
        "all_listings": """یہ **All Listings** کا صفحہ ہے۔ ہر product listing کو دیکھیں اور manage کریں:
- **Tabs**: All listings / Drafts (submit نہیں ہوئے) / Live on Amazon
- ہر row دکھاتا ہے: image، title، ASIN/SKU/barcode، brand، condition، handling time، cost، Amazon fees، estimated profit، status
- Status badges: Draft (submit نہیں ہوئے)، Live on Amazon، آپ کی review درکار، Amazon rejected
- "Add new product" کلک کریں Sourcing page جانے کے لیے
- "Filter listings" استعمال کریں status، category، وغیرہ کے لحاظ سے narrow down کرنے کے لیے

Drafts وہ products ہیں جو آپ کی queue میں ہیں لیکن ابھی Amazon نہیں بھیجے گئے۔ Live listings پہلے سے published ہیں۔""",
        
        "dashboard": """یہ **Dashboard** ہے — آپ کا Amazon business ایک نظر میں:
- **KPIs**: Monthly revenue، active listings، profit margin، items جو توجہ چاہتے ہیں
- **Products in progress**: Draft listings پر کام چل رہا ہے (ابھی live نہیں)
- **Account health**: Listing quality، Amazon sync، content quality scores (green=اچھا، orange=کام چاہیے، red=فوری)

Sidebar استعمال کریں navigate کرنے کے لیے Sourcing (products شامل کریں)، Listings (سب manage کریں)، یا دیگر tools تک۔""",
        
        "analytics": """یہ **Catalog Analytics** ہے — دیکھیں کیا آپ کے business کو drive کرتا ہے:
- **Revenue concentration**: % revenue top 5 products سے (high = diversify کرنے کا خیال کریں)
- **Best performer**: آپ کا سب سے زیادہ revenue والا product
- **Dead stock**: Products जिनہیں 90+ دن سے sales نہیں ملی (repricing یا remove کرنے کا خیال کریں)
- **Product performance table**: Revenue کی بنیاد پر ranked ساتھ units sold، profit، ROI، اور status

ROI = profit ÷ cost۔ زائدہ بہتر ہے۔ Dropdown استعمال کریں time period filter کرنے کے لیے۔""",
        
        "categories": """یہ **Category Explorer** ہے — صحیح Amazon category تلاش کریں:
- Amazon category tree browse کریں (expand کرنے کے لیے کلک کریں)
- ہر category دکھاتی ہے selling requirements، fees، اور required product attributes
- آپ کی listings by category دکھاتی ہے کہ آپ کے کتنے active listings ہیں ہر top-level category میں

صحیح category fees، visibility، اور جو info Amazon چاہتا ہے اس پر اثر ڈالتا ہے۔ "Browse full category tree" کلک کریں مزید کے لیے۔""",
        
        "variations": """یہ **Variations** کا صفحہ ہے — متعلقہ products کو ایک Amazon listing کے تحت گروپ کریں:
- ہر group = ایک parent listing multiple child options کے ساتھ (size، color، style)
- Customers تمام options دیکھتے ہیں ایک ہی product page پر
- "Create variation set" کلک کریں نئی group شروع کرنے کے لیے
- Status دکھاتا ہے کہ Amazon پر synced ہے یا review درکار ہے

Variations customers کو اجازت دیتا ہیں کہ وہ بغیر page چھوڑے اپنا option چنیں۔""",
        
        "image_studio": """یہ **AI Image Studio** ہے — AI کے ساتھ product images بنائیں:
- **Preview panel**: Generated image دکھاتا ہے، fidelity slider (زائدہ = واقعی product کے قریب)، standing instructions
- **Tabs**: Creative concepts / Main image (white bg) / Secondary images / A+ Content modules
- Settings: واقعی product سے کتنا قریب، image slot، secondary approach (AI suggest vs manual)، template
- "Generate image" کلک کریں پھر "Assign to listing slot" اپنے product میں شامل کرنے کے لیے

Main images ضروری ہیں pure white background پر Amazon rules کے مطابق۔""",
        
        "image_library": """یہ **Image Library** ہے — آپ کی تمام generated اور uploaded images:
- Filter کریں listing، image slot (Main، Image 1-4، A+)، یا status (Active، Draft، Queued) کی بنیاد پر
- Active = live listing کو assign، Draft = save ہوا لیکن assign نہیں، Queued = process ہو رہا ہے
- "Create new images" کلک کریں Image Studio جانے کے لیے
- "Upload image set" اور "Download as ZIP" bulk operations کے لیے""",
        
        "image_references": """یہ **Image References** ہے — reference images save کریں AI generation کی رہنمائی کے لیے:
- Images شامل کریں suppliers، competitors، یا brand guidelines سے
- یہ AI کو بتاتے ہیں کہ آپ کو کونسا style، angle، اور composition چاہیے
- Visual style set کریں (clean white، lifestyle، infographic)، brand colors، اور AI کے لیے notes
- "Generate test image" style preview کرنے کے لیے

References AI کو مدد کرتے ہیں آپ کی brand کی visual identity match کرنے میں۔""",
        
        "repricer": """یہ **Repricer** ہے — Amazon prices کو خود adjust کرتا ہے جب supplier costs بدلتے ہیں:
- **Profit rule** (سب products پر لاگو): Percentage (مثال: "20% margin رکھیں") یا Fixed amount (مثال: "$5 profit")
- System آپ کے supplier links کو دیکھتا ہے، سب سے سستا **in-stock** source تلاش کرتا ہے، آپ کی Amazon price set کرتا ہے margin برقرار رکھنے کے لیے
- ہر product دکھاتا ہے: موجودہ Amazon price، سب سے سستا in-stock supplier، status (Auto-priced / No source available)
- "Check supplier prices now" کلک کریں refresh کرنے کے لیے، "Save profit rule" update کرنے کے لیے

صرف in-stock sources consider کیے جاتے ہیں — out-of-stock competitors ignore کئے جاتے ہیں۔""",
        
        "amazon_policy": """Amazon کے sellers کے لیے جامع policies ہیں۔ اہم علاقے:

**Fees**: Referral fees (8-15% category کے لحاظ سے)، $39.99/month professional sellers کے لیے، FBA fulfillment fees۔

**Listing Requirements**: درست معلومات، کم از کم ایک image، مناسب category، content guidelines compliance۔

**Account Health**: Cancellation rate، defect rate، late shipment rate — Amazon selling restrict کر دیتا ہے اگر یہ standards سے نیچے گرجائیں۔

**Common Issues**: Pricing errors suppression trigger کرتے ہیں، keyword stuffing guidelines violate کرتا ہے، cross-shipping marketplaces کے درمیان allowed نہیں۔

مخصوص policy سوالات کے لیے، Amazon Seller Central کا Policy section چیک کریں یا Seller Support سے رابطہ کریں، کیونکہ policies بدلتی رہتی ہیں۔""",
        
        "pricing": """**Pricing & Repricing in Sellrix:**

**Profit Calculation**: 
- Profit = Sell Price - Cost
- Profit Margin % = (Profit / Sell Price) × 100

**Repricing Feature**:
- System آپ کے تمام supplier/competitor sources چیک کرتا ہے
- سب سے سستا اٹھاتا ہے جو "In Stock" ہو
- Minimum price calculate کرتا ہے آپ کا profit margin برقرار رکھنے کے لیے
- Profit set کریں percentage (20%) یا fixed amount ($5) کے طور پر

**مثال**: سب سے سستا supplier $10، 20% profit → تجویز کردہ price $12۔

Out-of-stock sources ignore کئے جاتے ہیں۔ اپنا rule Repricer page پر configure کریں۔""",
        
        "default": """میں آپ کا Sellrix AI assistant ہوں۔ میں مدد کر سکتا ہوں:

1. **یہ صفحہ** — پوچھیں "یہ صفحہ کس لیے ہے؟" یا "میں کیسے...؟"
2. **Amazon policies** — Fees، requirements، account health
3. **آپ کی listings** — Data، status، improvements
4. **Pricing/Repricing** — Profit calculations، margin rules

آپ کیا جاننا چاہتے ہیں؟ میں آپ کی زبان میں جواب دوں گا۔""",
    }
    
    # Function to get translated response
    def get_translated_response(page_key: str, response_type: str = "general") -> str:
        """Get pre-translated response for Urdu/Hindi."""
        if user_language in ["urdu", "hindi"]:
            # Dictionary uses: "page_key" for detailed, "page_key_general" for general
            if response_type == "detailed":
                key = page_key
            else:
                key = f"{page_key}_general"
            result = urdu_responses.get(key, urdu_responses.get("default"))
            print(f"DEBUG get_translated_response: page_key={page_key}, response_type={response_type}, key={key}, result={result[:50] if result else None}")
            return result
        return None
    
    if gemini_key:
        # Use real Gemini API if configured
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Build full message history
            chat_history = []
            for msg in messages_for_api:
                chat_history.append({
                    "role": msg["role"],
                    "parts": [{"text": msg["content"]}]
                })
            
            # Add current user message
            chat_history.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })
            
            # Call Gemini
            response = model.generate_content(
                chat_history,
                system_instruction=system_prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "max_output_tokens": 1024,
                }
            )
            
            answer = response.text if response.text else "I couldn't generate a response. Please try again."
        except Exception as exc:
            answer = f"I encountered an error calling the AI service: {str(exc)}. Please try again or check your API configuration."
    else:
        # Context-aware fallback responses based on page_context and user_message
        lower_msg = user_message.lower()
        page_lower = page_context.lower()
        
        # Check for Urdu/Hindi keywords directly in original message (not lowercased)
        urdu_keywords = ["کیسے", "شامل", "طریقہ", "منتج", "add", "product", "کیا", "کیا ہے", "کسی طرح"]
        hindi_keywords = ["कैसे", "शामिल", "तरीका", "उत्पाद", "क्या", "क्या है", "किस तरह"]
        has_urdu_hindi = any(kw in user_message for kw in urdu_keywords + hindi_keywords)
        
        # FIRST: Check for general topics (Amazon policy, pricing) - these apply regardless of page
        if any(word in lower_msg for word in ["amazon", "policy", "fee", "rule", "requirement", "amazon", "پالیسی", "فیس"]):
            answer = """Amazon has comprehensive policies for sellers. Key areas:

**Fees**: Referral fees (8-15% by category), $39.99/month for professional sellers, FBA fulfillment fees.

**Listing Requirements**: Accurate info, at least one image, proper category, content guidelines compliance.

**Account Health**: Cancellation rate, defect rate, late shipment rate — Amazon restricts selling if these fall below standards.

**Common Issues**: Pricing errors trigger suppression, keyword stuffing violates guidelines, cross-shipping between marketplaces not allowed.

For specific policy questions, check Amazon Seller Central's Policy section or contact Seller Support, as policies change."""
        
        elif any(word in lower_msg for word in ["price", "profit", "cost", "margin", "repricing", "قیمت", "منافع", "لاگت"]):
            answer = """**Pricing & Repricing in ListingHub:**

**Profit Calculation**: 
- Profit = Sell Price - Cost
- Profit Margin % = (Profit / Sell Price) × 100

**Repricing Feature**:
- System checks all your supplier/competitor sources
- Picks the cheapest one that's "In Stock"
- Calculates minimum price to maintain your profit margin
- Set profit as percentage (20%) or fixed amount ($5)

**Example**: Cheapest supplier $10, 20% profit → recommended price $12.

Out-of-stock sources are ignored. Configure your rule on the Repricer page."""
        
        # SECOND: Check for page-specific help requests
        elif "add new product" in page_lower or "sourcing" in page_lower:
            if any(word in lower_msg for word in ["how", "add", "product", "item", "kese", "kaise", "kitne", "tarika"]) or has_urdu_hindi:
                answer = """This is the **Add New Product** page. You have three ways to add products:

1. **Add One Product** — Paste a product link (from supplier, eBay, AliExpress, etc.) and we'll fetch the title and image automatically. Fill in your cost and sell price, then click "Fetch details & add to queue".

2. **Import from Spreadsheet** — Download the template, fill in your product data (source link, cost, etc.), upload the CSV/Excel file, and we'll process all rows at once.

3. **Fetch from eBay Seller** — Enter an eBay store link or username. We'll pull all their listings, auto-skip compliance-risk items, and let you choose which to add to your queue.

**Important**: The source link is required — we use it to get the product's title and photo automatically. Your product queue on the right shows everything you've added but not yet submitted to Amazon."""
            
            elif any(word in lower_msg for word in ["ebay", "seller", "store", "fetch", "pull"]):
                answer = """**Fetch from eBay Seller** lets you pull all products from one eBay seller's store:
- Paste their store link (like `https://www.ebay.com/str/storename`) or just their username
- Click "Fetch all products" — we'll scan their store page by page
- We auto-skip items with compliance risks (batteries, supplements, toys, etc.)
- You review the results, check/uncheck products, then click "Add selected to queue"
- Added products appear in your product queue on the right

The source link for each product will be the eBay listing URL."""
            
            elif any(word in lower_msg for word in ["import", "spreadsheet", "csv", "excel", "template", "spread sheet"]):
                answer = """**Import from Spreadsheet** adds many products at once:
1. Click "Download template" to get the exact column format
2. Fill in: Source link (required), Competitor ASIN/link, Product name, Brand, Cost (required), Sell price, Handling days, Barcode
3. Save as CSV or Excel (.xlsx)
4. Choose the file and click "Import rows"
5. We process each row, fetch titles/images from links, and add successful ones to your queue

Required columns: **Source link** and **Cost**. The template has all columns pre-labeled."""
            
            else:
                answer = """This is the **Add New Product** page. You have three ways to add products to your queue:
- **Add One Product**: Paste a link, we fetch title/image, you fill in pricing
- **Import from Spreadsheet**: Upload a CSV/Excel file with many products
- **Fetch from eBay Seller**: Enter a seller's store link, we pull all their listings

Your product queue on the right shows everything added but not yet submitted to Amazon. Click any item to review details."""
        
        elif "listing detail" in page_lower or "detail" in page_lower:
            if any(word in lower_msg for word in ["auto", "fix", "fill", "missing", "auto-fix", "آٹو", "فکس"]):
                answer = """**Auto-fill missing fields** (the "Auto-fix" button) automatically populates empty fields:
- It fetches data from your source link (title, brand, category, description, bullets)
- It uses AI to generate missing content (bullets, description, keywords)
- It shows a preview with 3 columns: ✓ Filled from source, 🤖 Filled by AI (review carefully), ⚠ Still needs your attention
- You review each item, then click "Submit to Amazon" when ready

Always review AI-generated content before submitting — it may need corrections."""
            
            elif any(word in lower_msg for word in ["ai", "content", "generate", "title", "bullet", "description", "keyword", "ایآئی", "کینکش"]):
                answer = """**Generate AI Content** creates listing text using AI:
- Click "Generate AI content" button
- It creates: Title (max 200 chars), 5 Bullet points, Full description (HTML allowed), Backend keywords (comma-separated, max 250 bytes)
- The generated content appears in the AI Content panel — you can edit it before saving
- Click "Save AI content to this listing" to apply it

Make sure your product name and brand are filled in first for best results."""
            
            elif any(word in lower_msg for word in ["image", "photo", "picture", "img", "تصویر", "فوٹو"]):
                answer = """**Images** on this page:
- The main product image shows in the sidebar (fetched from your source link)
- Click "Open Image Studio" to create new AI-generated images
- In the Images tab, you can assign images to slots: Main (white background), Image 1-4, A+ modules
- Amazon requires the Main image on pure white background

Use Image Studio for lifestyle shots, infographics, or A+ content modules."""
            
            else:
                answer = """This is the **Listing Detail** page. Review and complete all product details before submitting to Amazon:
- **Product Details tab**: Title, brand, condition, bullets, description, backend keywords
- **Images tab**: Manage product images (Main, lifestyle, A+ modules)
- **Offer & Pricing tab**: Your cost, sell price, handling time, barcode, pricing method
- **Safety & Compliance tab**: Compliance checks (restricted categories, claim risk, required documents)

Use **Auto-fix** to auto-populate from source link and AI, **Generate AI content** for listing text, and **Open Image Studio** for images. When everything looks good, click **Submit to Amazon**."""
        
        elif "all listings" in page_lower or "listings" in page_lower:
            answer = """This is the **All Listings** page. View and manage every product listing:
- **Tabs**: All listings / Drafts (not submitted) / Live on Amazon
- Each row shows: image, title, ASIN/SKU/barcode, brand, condition, handling time, cost, Amazon fees, estimated profit, status
- Status badges: Draft (not submitted), Live on Amazon, Needs your review, Amazon rejected
- Click "Add new product" to go to the Sourcing page
- Use "Filter listings" to narrow down by status, category, etc.

Drafts are products in your queue not yet sent to Amazon. Live listings are already published."""
        
        elif "dashboard" in page_lower:
            answer = """This is the **Dashboard** — your Amazon business at a glance:
- **KPIs**: Monthly revenue, active listings, profit margin, items needing attention
- **Products in progress**: Draft listings being worked on (not live yet)
- **Account health**: Listing quality, Amazon sync, content quality scores (green=good, orange=needs work, red=urgent)

Use the sidebar to navigate to Sourcing (add products), Listings (manage all), or other tools."""
        
        elif "analytics" in page_lower or "catalog" in page_lower:
            answer = """This is **Catalog Analytics** — see what drives your business:
- **Revenue concentration**: % of revenue from top 5 products (high = consider diversifying)
- **Best performer**: Your highest-revenue product
- **Dead stock**: Products with zero sales for 90+ days (consider repricing or removing)
- **Product performance table**: Ranked by revenue with units sold, profit, ROI, and status

ROI = profit ÷ cost. Higher is better. Filter by time period using the dropdown."""
        
        elif "category" in page_lower:
            answer = """This is the **Category Explorer** — find the right Amazon category:
- Browse the Amazon category tree (click to expand)
- Each category shows selling requirements, fees, and required product attributes
- Your listings by category shows how many active listings you have in each top-level category

The correct category affects fees, visibility, and what info Amazon requires. Click "Browse full category tree" for more."""
        
        elif "variation" in page_lower:
            answer = """This is the **Variations** page — group related products under one Amazon listing:
- Each group = one parent listing with multiple child options (size, color, style)
- Customers see all options on a single product page
- Click "Create variation set" to start a new group
- Status shows if synced on Amazon or needs review

Variations let customers pick their option without leaving the page."""
        
        elif "image studio" in page_lower:
            answer = """This is the **AI Image Studio** — create product images with AI:
- **Preview panel**: Shows generated image, fidelity slider (higher = closer to real product), standing instructions
- **Tabs**: Creative concepts / Main image (white bg) / Secondary images / A+ Content modules
- Settings: How close to real product, image slot, secondary approach (AI suggest vs manual), template
- Click "Generate image" then "Assign to listing slot" to add to your product

Main images MUST be on pure white background per Amazon rules."""
        
        elif "image library" in page_lower:
            answer = """This is the **Image Library** — all your generated and uploaded images:
- Filter by listing, image slot (Main, Image 1-4, A+), or status (Active, Draft, Queued)
- Active = assigned to a live listing, Draft = saved but not assigned, Queued = processing
- Click "Create new images" to go to Image Studio
- "Upload image set" and "Download as ZIP" for bulk operations"""
        
        elif "image references" in page_lower or "reference" in page_lower:
            answer = """This is **Image References** — save reference images to guide AI generation:
- Add images from suppliers, competitors, or brand guidelines
- They tell the AI what style, angle, and composition you want
- Set visual style (clean white, lifestyle, infographic), brand colors, and notes for AI
- "Generate test image" to preview the style

References help AI match your brand's visual identity."""
        
        elif "repricer" in page_lower:
            answer = """This is the **Repricer** — automatically adjust Amazon prices when supplier costs change:
- **Profit rule** (applies to all products): Percentage (e.g., "keep 20% margin") or Fixed amount (e.g., "$5 profit")
- System watches your supplier links, finds the cheapest **in-stock** source, sets your Amazon price to maintain margin
- Each product shows: current Amazon price, cheapest in-stock supplier, status (Auto-priced / No source available)
- Click "Check supplier prices now" to refresh, "Save profit rule" to update

Only in-stock sources are considered — out-of-stock competitors are ignored."""
        
        else:
            answer = """I'm your ListingHub AI assistant. I can help with:

1. **This page** — Ask "What is this page for?" or "How do I...?"
2. **Amazon policies** — Fees, requirements, account health
3. **Your listings** — Data, status, improvements
4. **Pricing/Repricing** — Profit calculations, margin rules

What would you like to know? I'll answer in the same language you asked."""
        return {"response": answer}


@app.post("/api/debug/translation")
def debug_translation(payload: ChatRequest):
    """Debug endpoint to test translation logic."""
    user_message = payload.user_message or ""
    page_context = payload.page_context or ""
    
    # Detect language
    def detect_language(text: str) -> str:
        if re.search(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
            return "urdu"
        if re.search(r'[\u0900-\u097F]', text):
            return "hindi"
        if re.search(r'[\u4e00-\u9fff]', text):
            return "chinese"
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text):
            return "japanese"
        if re.search(r'[\uAC00-\uD7AF]', text):
            return "korean"
        if re.search(r'[\u0600-\u06FF]', text):
            return "arabic"
        if re.search(r'\b(como|cómo|qué|que|dónde|donde|cuándo|cuando|por qué|porque|gracias|hola|ayuda|ayúdame)\b', text.lower()):
            return "spanish"
        if re.search(r'\b(comment|quoi|où|quand|pourquoi|merci|bonjour|aide|aidez-moi)\b', text.lower()):
            return "french"
        if re.search(r'\b(wie|was|wo|wann|warum|danke|hallo|hilfe|helfen)\b', text.lower()):
            return "german"
        if re.search(r'\b(comio|como|o quê|que|onde|quando|por que|obrigado|olá|ajuda|ajude-me)\b', text.lower()):
            return "portuguese"
        return "english"
    
    user_language = detect_language(user_message)
    lower_msg = user_message.lower()
    page_lower = page_context.lower()
    
    urdu_keywords = ["کیسے", "شامل", "طریقہ", "منتج", "add", "product", "کیا", "کیا ہے", "کسی طرح"]
    hindi_keywords = ["कैसे", "शामिल", "तरीका", "उत्पाद", "क्या", "क्या है", "किस तरह"]
    has_urdu_hindi = any(kw in user_message for kw in urdu_keywords + hindi_keywords)
    
    return {
        "user_message": user_message,
        "page_context": page_context,
        "detected_language": user_language,
        "lower_msg": lower_msg,
        "page_lower": page_lower,
        "has_urdu_hindi": has_urdu_hindi,
        "urdu_keywords_found": [kw for kw in urdu_keywords if kw in user_message],
        "hindi_keywords_found": [kw for kw in hindi_keywords if kw in user_message],
    }


@app.post("/api/ai/text/generate")
def generate_text(payload: GenerateTextRequest):
    """Return a mocked Gemini-style AI text generation payload.

    The actual Google Gemini API integration should use the environment
    variable GEMINI_API_KEY. This endpoint is kept placeholder-safe and
    returns structured listing text when no key is configured.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    live_mode = bool(gemini_key)

    if live_mode:
        # Production integration point:
        # call Google Gemini using GEMINI_API_KEY here and transform output
        # into a listing-ready schema.
        source = "gemini"
    else:
        source = "mock"

    title = f"{payload.brand} {payload.product_name}"
    bullets = [
        "Made for organized home and kitchen spaces",
        "Compact, durable and easy to store",
        "Designed to keep everyday items neat and accessible",
    ]
    description = (
        f"The {payload.product_name} from {payload.brand} is built for organized "
        f"shopping and storage routines in the {payload.category} category. "
        "It is designed for reliable daily use and made to help keep your "
        "items accessible, neat, and ready when needed."
    )
    keywords = [
        payload.product_name.lower(),
        payload.brand.lower(),
        payload.category.lower().replace(" & ", " "),
        "kitchen storage",
        "home organization",
    ]

    return {
        "title": title[:80],
        "bullet_points": bullets,
        "description": description,
        "backend_keywords": keywords,
        "fields": {
            "amazon_title_length": min(200, len(title)),
            "feature_bullets": len(bullets),
            "description_length": len(description),
            "keyword_count": len(keywords),
        },
        "source": source,
        "notes": "GEMINI_API_KEY is not set; returning mock Google Gemini-compatible text payload."
        if not live_mode else "Live Google Gemini integration hook is ready once GEMINI_API_KEY is configured.",
    }


@app.post("/api/ai/image/generate")
def generate_image(payload: ImageGenerateRequest):
    """Return a mocked Qwen-style image generation payload.

    The real integration expects an environment variable for a Qwen or
    DashScope-compatible model host, such as QWEN_API_KEY or DASHSCOPE_API_KEY.
    The code below keeps the feature UI and API surface complete while
    returning deterministic placeholder image metadata unless a key is set.
    """
    qwen_key = os.getenv("QWEN_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))
    live_mode = bool(qwen_key)

    slot = payload.image_slot or "Main"
    mode = payload.mode or "creative"
    if mode == "secondary":
        image_title = "Secondary image concept"
    elif mode == "main":
        image_title = "Main image"
    elif mode == "aplus":
        image_title = "A+ content module"
    else:
        image_title = "Creative variation"

    image_url = f"/static/images/mock-{payload.product_id}-{mode}.png"

    return {
        "images": [
            {
                "id": f"img-{payload.product_id}-{mode}-1",
                "image_url": image_url,
                "slot": slot,
                "mode": mode,
                "title": image_title,
                "size": "2000x2000" if mode == "main" else "1200x1200",
                "source": "qwen" if live_mode else "mock",
                "notes": "QWEN_API_KEY/DASHSCOPE_API_KEY is not set; returning mock Qwen-style image payload."
                if not live_mode else "Live Qwen/DashScope integration hook is ready once QWEN_API_KEY or DASHSCOPE_API_KEY is configured.",
                "standing_instructions": payload.standing_instructions,
                "fidelity": payload.fidelity,
                "concept_mode": payload.concept_mode,
            }
        ]
    }


@app.get("/api/repricer/products")
def repricer_products():
    """Return the in-memory repricer dataset. The sources are manually editable
    in the UI for now. A later automated integration can replace the mock list
    with a supplier or competitor feed source, but this contract already
    expresses the correct multi-source setup and active-fallback selection.
    """
    return repricer_payload()


@app.patch("/api/repricer/products/{product_id}/sources/{source_id}")
def update_repricer_source(product_id: str, source_id: str, payload: RepricerSourceStockUpdateRequest):
    """Update one source's stock state and recompute the active cheapest in-stock
    source for the product. This is the server-side proof of the fallback rule.
    """
    product = next((p for p in REPRICER_PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    source = next((s for s in product["sources"] if s["id"] == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source["stock_status"] = payload.stock_status
    source["last_checked"] = datetime.utcnow().isoformat() + "Z"

    enriched = enrich_repricing_product(product)
    return {"product": enriched, "message": "Source stock status updated. Cheapest in-stock source recalculated."}


# ===== Amazon SP-API Endpoints =====

def get_current_user_id() -> int:
    """Get current user ID from token. In production, use proper auth middleware."""
    # For now, return the first user (demo mode)
    with get_connection() as conn:
        user = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
        return user["id"] if user else 1


@app.get("/api/amazon/credentials", response_model=list[AmazonCredentialsResponse])
def list_amazon_credentials():
    """List all configured Amazon SP-API credentials."""
    user_id = get_current_user_id()
    with get_connection() as conn:
        creds = conn.execute(
            "SELECT * FROM amazon_credentials WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    return [dict(c) for c in creds]


@app.post("/api/amazon/credentials", response_model=AmazonCredentialsResponse)
def save_amazon_credentials(payload: AmazonCredentialsRequest):
    """Save or update Amazon SP-API credentials."""
    user_id = get_current_user_id()
    now = datetime.utcnow().isoformat()
    
    with get_connection() as conn:
        # Check if credentials exist for this marketplace
        existing = conn.execute(
            "SELECT id FROM amazon_credentials WHERE user_id = ? AND marketplace_id = ?",
            (user_id, payload.marketplace_id)
        ).fetchone()
        
        if existing:
            conn.execute(
                """
                UPDATE amazon_credentials 
                SET client_id = ?, client_secret = ?, refresh_token = ?, region = ?, 
                    marketplace_name = ?, is_active = 1, updated_at = ?
                WHERE id = ?
                """,
                (payload.client_id, payload.client_secret, payload.refresh_token,
                 payload.region, payload.marketplace_name, now, existing["id"])
            )
            cred_id = existing["id"]
        else:
            cur = conn.execute(
                """
                INSERT INTO amazon_credentials (user_id, marketplace_id, marketplace_name, 
                    client_id, client_secret, refresh_token, region, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (user_id, payload.marketplace_id, payload.marketplace_name,
                 payload.client_id, payload.client_secret, payload.refresh_token,
                 payload.region, now, now)
            )
            cred_id = cur.lastrowid
        conn.commit()
        
        cred = conn.execute("SELECT * FROM amazon_credentials WHERE id = ?", (cred_id,)).fetchone()
    
    return dict(cred)


@app.delete("/api/amazon/credentials/{cred_id}")
def delete_amazon_credentials(cred_id: int):
    """Delete Amazon SP-API credentials."""
    user_id = get_current_user_id()
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM amazon_credentials WHERE id = ? AND user_id = ?",
            (cred_id, user_id)
        )
        conn.commit()
    return {"message": "Credentials deleted"}


@app.get("/api/amazon/credentials/status")
def amazon_credentials_status():
    """Check if Amazon SP-API credentials are configured and valid."""
    user_id = get_current_user_id()
    with get_connection() as conn:
        cred = conn.execute(
            "SELECT * FROM amazon_credentials WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
    
    if not cred:
        return {
            "configured": False,
            "message": "No Amazon SP-API credentials configured. Go to Settings to add your Client ID, Client Secret, and Refresh Token.",
            "setup_steps": [
                "1. Go to Amazon Seller Central > Apps & Services > Develop Apps",
                "2. Click 'Register a new application'",
                "3. Fill in app name, description, and redirect URI",
                "4. Add 'Selling Partner API' roles: Orders, Listings, Catalog, Reports",
                "5. Save to get Client ID and Client Secret",
                "6. Click 'Authorize' next to your app to get the Refresh Token",
                "7. Enter all three values in this app's Amazon Integration settings"
            ]
        }
    
    # Check if using mock credentials
    is_mock = cred["client_id"].startswith("MOCK_") if cred["client_id"] else False
    
    return {
        "configured": True,
        "is_mock": is_mock,
        "marketplace": cred["marketplace_name"],
        "region": cred["region"],
        "message": "Using mock/demo mode. Add real credentials for live data." if is_mock else "Credentials configured. Ready for live SP-API calls.",
        "cred_id": cred["id"]
    }


@app.post("/api/amazon/listings/publish")
def publish_listing(payload: PublishListingRequest):
    """Publish a listing to Amazon via SP-API."""
    user_id = get_current_user_id()
    
    # Get credentials
    with get_connection() as conn:
        cred = conn.execute(
            "SELECT * FROM amazon_credentials WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
    
    if not cred:
        raise HTTPException(
            status_code=400, 
            detail="No Amazon SP-API credentials configured. Please add credentials first."
        )
    
    # Initialize SP-API client
    client = SPApiClient(dict(cred))
    
    # Prepare listing data for SP-API
    listing_data = {
        "sku": payload.sku,
        "product_type": "PRODUCT",
        "requirements": "LISTING",
        "attributes": {
            "item_name": [{"value": payload.title, "language_tag": "en_US"}],
            "brand": [{"value": payload.brand, "language_tag": "en_US"}],
            "list_price": [{"value": str(payload.price), "currency": "USD"}],
            "main_image": [{"value": payload.images[0], "language_tag": "en_US"}] if payload.images else [],
            "bullet_points": [{"value": "\n".join(payload.bullet_points), "language_tag": "en_US"}],
            "product_description": [{"value": payload.description, "language_tag": "en_US"}],
            "generic_keywords": [{"value": ", ".join(payload.backend_keywords), "language_tag": "en_US"}],
            "condition_type": [{"value": payload.condition_type, "language_tag": "en_US"}],
            "fulfillment_latency": [{"value": payload.fulfillment_latency, "language_tag": "en_US"}]
        }
    }
    
    # Add ASIN if provided (update existing)
    if payload.asin:
        listing_data["asin"] = payload.asin
    
    # Call SP-API
    endpoint = f"listings/2021-08-01/items/{payload.sku}"
    if payload.asin:
        endpoint = f"listings/2021-08-01/items/{payload.sku}?marketplaceIds={cred['marketplace_id']}"
    
    result = client._make_request("PUT", endpoint, listing_data)
    
    # Save/update local listing record
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM amazon_listings WHERE user_id = ? AND sku = ?",
            (user_id, payload.sku)
        ).fetchone()
        
        local_data = {
            "title": payload.title,
            "brand": payload.brand,
            "description": payload.description,
            "bullet_points": payload.bullet_points,
            "backend_keywords": payload.backend_keywords,
            "price": payload.price,
            "images": payload.images,
            "category_id": payload.category_id,
            "condition_type": payload.condition_type,
            "fulfillment_latency": payload.fulfillment_latency
        }
        
        if existing:
            conn.execute(
                """
                UPDATE amazon_listings 
                SET asin = ?, title = ?, brand = ?, price = ?, local_data = ?, 
                    status = 'published', published_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (payload.asin, payload.title, payload.brand, payload.price, 
                 json.dumps(local_data), now, now, existing["id"])
            )
            listing_id = existing["id"]
        else:
            cur = conn.execute(
                """
                INSERT INTO amazon_listings (user_id, sku, asin, title, brand, price, 
                    local_data, status, published_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'published', ?, ?, ?)
                """,
                (user_id, payload.sku, payload.asin, payload.title, payload.brand, 
                 payload.price, json.dumps(local_data), now, now, now)
            )
            listing_id = cur.lastrowid
        conn.commit()
    
    return {
        "success": True,
        "listing_id": listing_id,
        "sku": payload.sku,
        "asin": result.get("asin") or payload.asin,
        "submission_id": result.get("submission_id"),
        "status": result.get("status"),
        "message": "Listing submitted to Amazon" if not cred["client_id"].startswith("MOCK_") else "Listing published (mock mode - no real API call made)"
    }


@app.post("/api/amazon/listings/compare", response_model=CompareListingResponse)
def compare_listing(payload: CompareListingRequest):
    """Compare local listing data with Amazon's live version."""
    user_id = get_current_user_id()
    
    # Get local listing
    with get_connection() as conn:
        listing = conn.execute(
            "SELECT * FROM amazon_listings WHERE user_id = ? AND id = ?",
            (user_id, payload.listing_id)
        ).fetchone()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    local_data = json.loads(listing["local_data"]) if listing["local_data"] else {}
    
    # Get credentials
    with get_connection() as conn:
        cred = conn.execute(
            "SELECT * FROM amazon_credentials WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
    
    if not cred:
        raise HTTPException(
            status_code=400, 
            detail="No Amazon SP-API credentials configured. Please add credentials first."
        )
    
    # Initialize SP-API client and fetch Amazon data
    client = SPApiClient(dict(cred))
    
    asin = listing["asin"] or listing["sku"]
    result = client._make_request("GET", f"listings/2021-08-01/items/{asin}")
    
    amazon_attrs = result.get("attributes", {})
    
    # Compare fields
    fields_to_compare = [
        ("title", local_data.get("title", ""), amazon_attrs.get("item_name", [{}])[0].get("value", "")),
        ("brand", local_data.get("brand", ""), amazon_attrs.get("brand", [{}])[0].get("value", "")),
        ("price", local_data.get("price", 0), float(amazon_attrs.get("list_price", [{}])[0].get("value", 0) or 0)),
        ("description", local_data.get("description", ""), amazon_attrs.get("product_description", [{}])[0].get("value", "")),
        ("bullet_points", local_data.get("bullet_points", []), amazon_attrs.get("bullet_points", [{}])[0].get("value", "").split("\n") if amazon_attrs.get("bullet_points") else []),
        ("backend_keywords", local_data.get("backend_keywords", []), amazon_attrs.get("generic_keywords", [{}])[0].get("value", "").split(", ") if amazon_attrs.get("generic_keywords") else []),
        ("condition_type", local_data.get("condition_type", "New"), amazon_attrs.get("condition_type", [{}])[0].get("value", "New")),
        ("fulfillment_latency", local_data.get("fulfillment_latency", "2-3 days"), amazon_attrs.get("fulfillment_latency", [{}])[0].get("value", "2-3 days")),
    ]
    
    compare_fields = []
    for field_name, local_val, amazon_val in fields_to_compare:
        # Normalize for comparison
        if isinstance(local_val, list):
            local_norm = sorted([v.strip().lower() for v in local_val if v])
        else:
            local_norm = str(local_val).strip().lower()
        
        if isinstance(amazon_val, list):
            amazon_norm = sorted([v.strip().lower() for v in amazon_val if v])
        else:
            amazon_norm = str(amazon_val).strip().lower()
        
        is_different = local_norm != amazon_norm
        
        compare_fields.append(CompareField(
            field=field_name,
            local_value=local_val,
            amazon_value=amazon_val,
            is_different=is_different
        ))
    
    # Update local record with Amazon data for future reference
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE amazon_listings SET amazon_data = ?, last_synced = ?, updated_at = ? WHERE id = ?",
            (json.dumps(result.get("attributes", {})), now, now, payload.listing_id)
        )
        conn.commit()
    
    return CompareListingResponse(
        listing_id=payload.listing_id,
        sku=listing["sku"],
        asin=listing["asin"],
        fields=compare_fields
    )


@app.post("/api/amazon/listings/sync-from-amazon/{listing_id}")
def sync_listing_from_amazon(listing_id: int, field: str, use_amazon_value: bool):
    """Sync a specific field from Amazon to local (or vice versa - not implemented here)."""
    user_id = get_current_user_id()
    
    with get_connection() as conn:
        listing = conn.execute(
            "SELECT * FROM amazon_listings WHERE user_id = ? AND id = ?",
            (user_id, listing_id)
        ).fetchone()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    local_data = json.loads(listing["local_data"]) if listing["local_data"] else {}
    amazon_data = json.loads(listing["amazon_data"]) if listing["amazon_data"] else {}
    
    field_mapping = {
        "title": ("item_name", lambda x: x[0].get("value", "") if x else ""),
        "brand": ("brand", lambda x: x[0].get("value", "") if x else ""),
        "price": ("list_price", lambda x: float(x[0].get("value", 0) or 0) if x else 0),
        "description": ("product_description", lambda x: x[0].get("value", "") if x else ""),
        "bullet_points": ("bullet_points", lambda x: x[0].get("value", "").split("\n") if x else []),
        "backend_keywords": ("generic_keywords", lambda x: x[0].get("value", "").split(", ") if x else []),
        "condition_type": ("condition_type", lambda x: x[0].get("value", "New") if x else "New"),
        "fulfillment_latency": ("fulfillment_latency", lambda x: x[0].get("value", "2-3 days") if x else "2-3 days"),
    }
    
    if field not in field_mapping:
        raise HTTPException(status_code=400, detail=f"Unknown field: {field}")
    
    amazon_key, extractor = field_mapping[field]
    amazon_value = extractor(amazon_data.get(amazon_key))
    
    if use_amazon_value:
        local_data[field] = amazon_value
    # If not use_amazon_value, we'd push local to Amazon (not implemented here)
    
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE amazon_listings SET local_data = ?, updated_at = ? WHERE id = ?",
            (json.dumps(local_data), now, listing_id)
        )
        conn.commit()
    
    return {
        "success": True,
        "field": field,
        "new_value": amazon_value if use_amazon_value else local_data.get(field),
        "message": f"Updated {field} from Amazon" if use_amazon_value else f"Kept local value for {field}"
    }


@app.get("/api/amazon/orders", response_model=OrdersListResponse)
def list_orders(
    page: int = 1,
    page_size: int = 25,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    sort_by: str = "purchase_date",
    sort_order: str = "desc",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """List orders with pagination, search, filtering, and sorting."""
    user_id = get_current_user_id()
    
    # Build query
    where_clauses = ["user_id = ?"]
    params = [user_id]
    
    if search:
        where_clauses.append("(amazon_order_id LIKE ? OR shipping_address_city LIKE ? OR shipping_address_state LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    if status_filter:
        where_clauses.append("order_status = ?")
        params.append(status_filter)
    
    if date_from:
        where_clauses.append("purchase_date >= ?")
        params.append(date_from)
    
    if date_to:
        where_clauses.append("purchase_date <= ?")
        params.append(date_to)
    
    where_sql = " AND ".join(where_clauses)
    
    # Validate sort_by
    allowed_sort = ["purchase_date", "order_total", "profit", "roi_percent", "amazon_order_id", "shipping_address_city"]
    if sort_by not in allowed_sort:
        sort_by = "purchase_date"
    
    sort_order_sql = "DESC" if sort_order.lower() == "desc" else "ASC"
    
    with get_connection() as conn:
        # Get total count
        total = conn.execute(
            f"SELECT COUNT(*) as cnt FROM orders WHERE {where_sql}",
            params
        ).fetchone()["cnt"]
        
        # Get orders
        offset = (page - 1) * page_size
        orders = conn.execute(
            f"""
            SELECT * FROM orders 
            WHERE {where_sql}
            ORDER BY {sort_by} {sort_order_sql}
            LIMIT ? OFFSET ?
            """,
            params + [page_size, offset]
        ).fetchall()
        
        # Get items for each order
        order_ids = [o["id"] for o in orders]
        items_map = {}
        if order_ids:
            placeholders = ",".join("?" * len(order_ids))
            items = conn.execute(
                f"SELECT * FROM order_items WHERE order_id IN ({placeholders})",
                order_ids
            ).fetchall()
            for item in items:
                oid = item["order_id"]
                if oid not in items_map:
                    items_map[oid] = []
                items_map[oid].append(dict(item))
    
    # Build response
    order_responses = []
    for order in orders:
        order_dict = dict(order)
        order_responses.append(OrderResponse(
            **order_dict,
            items=[OrderItemResponse(**item) for item in items_map.get(order["id"], [])]
        ))
    
    return OrdersListResponse(
        orders=order_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@app.post("/api/amazon/orders/sync")
def sync_orders():
    """Sync orders from Amazon SP-API."""
    user_id = get_current_user_id()
    
    # Get credentials
    with get_connection() as conn:
        cred = conn.execute(
            "SELECT * FROM amazon_credentials WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
    
    if not cred:
        raise HTTPException(
            status_code=400, 
            detail="No Amazon SP-API credentials configured. Please add credentials first."
        )
    
    # Initialize SP-API client
    client = SPApiClient(dict(cred))
    
    # Fetch orders from SP-API
    result = client._make_request("GET", "orders/v0/orders")
    orders_data = result.get("Orders", [])
    
    synced = 0
    updated = 0
    now = datetime.utcnow().isoformat()
    
    with get_connection() as conn:
        for order_data in orders_data:
            amazon_order_id = order_data["AmazonOrderId"]
            
            # Check if order exists
            existing = conn.execute(
                "SELECT id FROM orders WHERE user_id = ? AND amazon_order_id = ?",
                (user_id, amazon_order_id)
            ).fetchone()
            
            # Calculate fees and profit (simplified)
            order_total = float(order_data["OrderTotal"]["Amount"])
            # Estimate Amazon fees (15% referral + FBA fees if AFN)
            is_fba = order_data.get("FulfillmentChannel") == "AFN"
            estimated_fees = order_total * 0.15
            if is_fba:
                estimated_fees += 3.50  # Rough FBA fee estimate
            profit = order_total - estimated_fees
            roi = (profit / estimated_fees * 100) if estimated_fees > 0 else 0
            
            shipping = order_data.get("ShippingAddress", {})
            
            if existing:
                conn.execute(
                    """
                    UPDATE orders SET
                        order_status = ?, order_total = ?, amazon_fees = ?, profit = ?, roi_percent = ?,
                        fulfillment_channel = ?, sales_channel = ?, shipping_address_city = ?,
                        shipping_address_state = ?, shipping_address_country = ?, shipping_address_postal_code = ?,
                        number_of_items = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (order_data["OrderStatus"], order_total, estimated_fees, profit, roi,
                     order_data.get("FulfillmentChannel"), order_data.get("SalesChannel"),
                     shipping.get("City"), shipping.get("StateOrRegion"), shipping.get("CountryCode"),
                     shipping.get("PostalCode"), order_data.get("NumberOfItemsShipped", 0) + order_data.get("NumberOfItemsUnshipped", 0),
                     now, existing["id"])
                )
                order_id = existing["id"]
                updated += 1
            else:
                cur = conn.execute(
                    """
                    INSERT INTO orders (user_id, amazon_order_id, purchase_date, order_status,
                        fulfillment_channel, sales_channel, order_total, currency,
                        shipping_address_city, shipping_address_state, shipping_address_country,
                        shipping_address_postal_code, number_of_items, amazon_fees, profit, roi_percent,
                        created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, amazon_order_id, order_data["PurchaseDate"], order_data["OrderStatus"],
                     order_data.get("FulfillmentChannel"), order_data.get("SalesChannel"),
                     order_total, order_data["OrderTotal"]["CurrencyCode"],
                     shipping.get("City"), shipping.get("StateOrRegion"), shipping.get("CountryCode"),
                     shipping.get("PostalCode"), order_data.get("NumberOfItemsShipped", 0) + order_data.get("NumberOfItemsUnshipped", 0),
                     estimated_fees, profit, roi, now, now)
                )
                order_id = cur.lastrowid
                synced += 1
            
            # Fetch and save order items
            items_result = client._make_request("GET", f"orders/v0/orders/{amazon_order_id}/orderItems")
            for item_data in items_result.get("OrderItems", []):
                item_existing = conn.execute(
                    "SELECT id FROM order_items WHERE order_id = ? AND asin = ? AND sku = ?",
                    (order_id, item_data.get("ASIN"), item_data.get("SellerSKU"))
                ).fetchone()
                
                if not item_existing:
                    conn.execute(
                        """
                        INSERT INTO order_items (order_id, asin, sku, title, quantity,
                            item_price, item_tax, shipping_price, shipping_tax,
                            promotion_discount, promotion_discount_tax)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (order_id, item_data.get("ASIN"), item_data.get("SellerSKU"),
                         item_data.get("Title"), item_data.get("QuantityOrdered", 1),
                         float(item_data["ItemPrice"]["Amount"]), float(item_data["ItemTax"]["Amount"]),
                         float(item_data["ShippingPrice"]["Amount"]), float(item_data["ShippingTax"]["Amount"]),
                         float(item_data["PromotionDiscount"]["Amount"]), float(item_data["PromotionDiscountTax"]["Amount"]))
                    )
        
        conn.commit()
    
    return {
        "success": True,
        "synced": synced,
        "updated": updated,
        "total_fetched": len(orders_data),
        "message": f"Synced {synced} new orders, updated {updated} existing orders" if not cred["client_id"].startswith("MOCK_") else f"Mock sync: {synced} new, {updated} updated (no real API call)"
    }


@app.get("/api/amazon/orders/stats")
def orders_stats():
    """Get order statistics for dashboard."""
    user_id = get_current_user_id()
    
    with get_connection() as conn:
        stats = conn.execute(
            """
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN order_status = 'Shipped' THEN 1 ELSE 0 END) as shipped,
                SUM(CASE WHEN order_status = 'Unshipped' THEN 1 ELSE 0 END) as unshipped,
                SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(order_total) as total_revenue,
                SUM(amazon_fees) as total_fees,
                SUM(profit) as total_profit,
                AVG(roi_percent) as avg_roi
            FROM orders WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()
    
    return dict(stats) if stats else {
        "total_orders": 0, "shipped": 0, "unshipped": 0, "cancelled": 0,
        "total_revenue": 0, "total_fees": 0, "total_profit": 0, "avg_roi": 0
    }

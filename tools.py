import json
from typing import Optional, Dict, Any, Union, List
from langchain_core.tools import tool

# Consolidated Knowledge Base combining pricing data and knowledge facts
KNOWLEDGE_BASE: Dict[str, Any] = {
  "pricing": {
    "meta": {
      "project": "MGC Aurora Heights",
      "developer": "MGC Developments (Mian Group of Chakwal)",
      "currency": "PKR",
      "residential_floors": [4, 22],
      "commercial_floors": [1, 3],
      "total_residential_units": 418,
      "documents": {
        "brochure": {"file": "01_mgc_aurora_heights_brochure.md", "issued": "2025-03"},
        "price_list": {"file": "02_price_list_payment_plan.md", "effective": "2025-04-01", "supersedes": "January 2025 list"},
        "policy_faq": {"file": "03_booking_policy_faq.md", "version": "2.1", "updated": "2025-05"}
      },
      "price_protection_deadline": "2025-06-30"
    },
    "unit_types": {
      "studio": {"label": "Studio", "bedrooms": 0, "area_sqft": 480, "total_units": 64, "blocks": ["A"], "margalla_eligible": False, "corner_type": False},
      "1bed_standard": {"label": "1-Bed Standard", "bedrooms": 1, "area_sqft": 720, "total_units": 96, "blocks": ["A", "B"], "margalla_eligible": False, "corner_type": False},
      "2bed_standard": {"label": "2-Bed Standard", "bedrooms": 2, "area_sqft": 1150, "total_units": 128, "blocks": ["A", "B"], "margalla_eligible": True, "corner_type": False},
      "2bed_corner": {"label": "2-Bed Corner", "bedrooms": 2, "area_sqft": 1310, "total_units": 42, "blocks": ["B"], "margalla_eligible": True, "corner_type": True},
      "3bed_executive": {"label": "3-Bed Executive", "bedrooms": 3, "area_sqft": 1880, "total_units": 66, "blocks": ["B"], "margalla_eligible": True, "corner_type": False},
      "4bed_penthouse": {"label": "4-Bed Penthouse", "bedrooms": 4, "area_sqft": 3400, "total_units": 22, "blocks": ["B"], "margalla_eligible": True, "corner_type": False, "floors": [20, 22]}
    },
    "prices": [
      {"unit_type": "studio", "block": "A", "price_per_sqft": 18000, "base_price": 8640000},
      {"unit_type": "1bed_standard", "block": "A", "price_per_sqft": 18500, "base_price": 13320000},
      {"unit_type": "2bed_standard", "block": "A", "price_per_sqft": 19000, "base_price": 21850000},
      {"unit_type": "1bed_standard", "block": "B", "price_per_sqft": 19000, "base_price": 13680000},
      {"unit_type": "2bed_standard", "block": "B", "price_per_sqft": 19500, "base_price": 22425000},
      {"unit_type": "2bed_corner", "block": "B", "price_per_sqft": 20500, "base_price": 26855000},
      {"unit_type": "3bed_executive", "block": "B", "price_per_sqft": 21000, "base_price": 39480000},
      {"unit_type": "4bed_penthouse", "block": "B", "price_per_sqft": 26000, "base_price": 88400000}
    ],
    "location_premiums": {
      "cumulative": True,
      "applied_on": "base_price (undiscounted)",
      "floor_bands": [
        {"from": 4, "to": 12, "pct": 0, "note": "no premium listed"},
        {"from": 13, "to": 19, "pct": 4},
        {"from": 20, "to": 22, "pct": 7}
      ],
      "corner_pct": 3,
      "margalla_pct": 6
    },
    "discounts": {
      "applied_on": "base_price only; location premiums are never discounted",
      "payment_options": {
        "standard": {"pct": 0},
        "full_payment": {"pct": 12, "doc_label": "Full cash payment"},
        "fifty_percent_upfront": {"pct": 6, "doc_label": "50% upfront"}
      },
      "overseas_pct": 2,
      "second_unit_pct": 1.5,
      "not_applicable_to": ["commercial podium units"]
    },
    "payment_plan_standard": {
      "years": 4,
      "milestones": [
        {"name": "Booking / token", "pct": 10},
        {"name": "Confirmation (due within 45 days of booking)", "pct": 10},
        {"name": "Quarterly instalment", "pct": 3.75, "count": 16},
        {"name": "On possession", "pct": 20}
      ]
    },
    "other_charges": {
      "utility_connection_per_unit": 285000,
      "parking_mandatory_one_per_unit": 1450000,
      "parking_additional_slot": 1650000,
      "maintenance_advance_months": 12,
      "maintenance_rate_per_sqft_per_month": 9.5
    },
    "transfer_fee_candidates": [
      {
        "rate_pct": 2.5,
        "source": "03_booking_policy_faq.md > Transfers",
        "doc_date": "v2.1, May 2025",
        "conditions": "after confirmation payment and at least 4 quarterly instalments cleared"
      },
      {
        "rate_pct": 2.0,
        "source": "02_price_list_payment_plan.md > Other Charges",
        "doc_date": "effective 1 April 2025",
        "conditions": "labelled 'before possession'"
      }
    ]
  },
  "knowledge": [
    {
      "id": "transfer_fee",
      "status": "conflict",
      "keywords": ["transfer", "transfer fee", "resale", "assign", "power of attorney", "poa", "sell unit", "transfer eligibility"],
      "answer": "The documents disagree: the booking policy (v2.1, May 2025) says 2.5% of the current list price; the price list (effective 1 April 2025) says 2% of the current list price for transfers before possession.",
      "details": {
        "policy_conditions": "Allowed only after the confirmation payment is made and at least four quarterly instalments have cleared. Both parties must attend head office in person; transfer by power of attorney needs prior written MGC management approval. Overseas buyers are exempt from the in-person requirement if documents are attested by the relevant Pakistani mission.",
        "precedence": "Neither document states which one takes precedence. The policy document is the later-dated one."
      },
      "sources": ["03_booking_policy_faq.md > Transfers", "02_price_list_payment_plan.md > Other Charges"],
      "agent_instruction": "Never silently pick one. Give both figures with their sources, say the policy doc is newer but precedence is not stated, and advise confirming with the sales office. Use estimate_transfer_fee for amounts."
    },
    {
      "id": "rental_yield",
      "status": "not_published",
      "keywords": ["rental", "yield", "rent", "roi", "return", "investment", "appreciation", "income"],
      "answer": "MGC does not publish rental yield projections, and sales staff are told not to give projections verbally.",
      "details": {"escalation": "Direct such queries to the marketing manager."},
      "sources": ["03_booking_policy_faq.md > Frequently Asked"],
      "agent_instruction": "Do not estimate or invent any yield, ROI or appreciation figure. Say it is not published and refer the user to the marketing manager via the sales office."
    },
    {
      "id": "anchor_tenant",
      "status": "unconfirmed",
      "keywords": ["anchor", "tenant", "tenancy", "retail", "brands", "mall"],
      "answer": "No anchor tenant has been confirmed as of the brochure's issue date (March 2025). Anchor tenancy discussions are ongoing.",
      "details": {},
      "sources": ["01_mgc_aurora_heights_brochure.md > Commercial Podium"],
      "agent_instruction": "Say plainly that no anchor tenant is confirmed. Do not name or speculate about any brand."
    },
    {
      "id": "gas_connection",
      "status": "unconfirmed",
      "keywords": ["gas", "sui", "sngpl", "connection"],
      "answer": "A Sui gas connection has been applied for. No confirmed timeline is available.",
      "details": {},
      "sources": ["03_booking_policy_faq.md > Frequently Asked"],
      "agent_instruction": "Do not promise gas availability or give a date."
    },
    {
      "id": "home_loan",
      "status": "partial",
      "keywords": ["loan", "mortgage", "financing", "finance", "bank", "markup", "mark-up", "interest", "installment bank"],
      "answer": "MGC has arrangements in principle with two banks. Terms, eligibility and mark-up rates are set by the bank, not by MGC.",
      "details": {"restriction": "Sales staff must not quote mark-up rates. The banks are not named in the documents."},
      "sources": ["03_booking_policy_faq.md > Frequently Asked"],
      "agent_instruction": "Do not quote rates, name banks, or promise approval."
    },
    {
      "id": "booking_process",
      "status": "confirmed",
      "keywords": ["book", "booking", "how to buy", "process", "steps", "form", "cnic", "passport", "allocation letter", "token", "sale agreement", "escrow"],
      "answer": "1) Select a unit and submit Form MGC-B1 with CNIC copy (passport for overseas buyers). 2) Pay the token into the project escrow account; cash is not accepted above PKR 500,000. 3) Allocation letter is issued within 7 working days of the token clearing. 4) Confirmation payment is due within 45 days. 5) On receiving the confirmation payment the buyer signs the Sale Agreement.",
      "details": {"booking_confirmed_when": "A booking is confirmed only once the token clears into the MGC escrow account at the project's designated bank."},
      "sources": ["03_booking_policy_faq.md > Booking Process", "02_price_list_payment_plan.md > Notes"],
      "agent_instruction": ""
    },
    {
      "id": "cancellation_refund",
      "status": "confirmed",
      "keywords": ["cancel", "cancellation", "refund", "refundable", "withdraw", "money back", "token refund"],
      "answer": "Cancel within 30 days of booking: token refunded less a PKR 75,000 processing deduction. After 30 days the token is non-refundable.",
      "details": {},
      "sources": ["03_booking_policy_faq.md > Cancellations and Refunds", "02_price_list_payment_plan.md > Standard Payment Plan"],
      "agent_instruction": ""
    },
    {
      "id": "default_cancellation",
      "status": "confirmed",
      "keywords": ["default", "miss", "missed", "late", "instalment", "installment", "liquidated damages", "penalty"],
      "answer": "If a buyer defaults on three consecutive quarterly instalments, MGC may cancel the allocation and refund all amounts paid less 15% of the total unit price as liquidated damages, within 180 days.",
      "details": {},
      "sources": ["03_booking_policy_faq.md > Cancellations and Refunds"],
      "agent_instruction": "Late-payment surcharges are not mentioned in the documents; do not invent any."
    },
    {
      "id": "overseas_buyers",
      "status": "confirmed",
      "keywords": ["overseas", "abroad", "roshan", "rda", "remittance", "expat", "nrp", "foreign"],
      "answer": "Overseas Pakistanis may book remotely. Payments must come from a Roshan Digital Account or a declared foreign remittance channel. They get an additional 2% discount (on base price, stackable with the full-payment or 50%-upfront discounts) and are exempt from the in-person transfer requirement if documents are attested by the relevant Pakistani mission.",
      "details": {"note": "The price list mentions only the Roshan Digital Account for the 2% discount; the policy also allows declared foreign remittance channels."},
      "sources": ["03_booking_policy_faq.md > Overseas Buyers", "02_price_list_payment_plan.md > Discounts"],
      "agent_instruction": "Use quote_unit_price with overseas_buyer=true for amounts."
    },
    {
      "id": "possession",
      "status": "partial",
      "keywords": ["possession", "handover", "hand over", "delivery", "holding charge", "completion certificate", "move in"],
      "answer": "Possession is offered once the completion certificate is issued and all dues are cleared. Buyers get 30 days' notice. A holding charge of PKR 25,000 per month applies if possession is not taken within 60 days of the notice. Target for Block A is Q3 2027.",
      "details": {"block_b": "A Block B possession target is NOT stated. Block B structural completion is two quarters after Block A (Q1 2027)."},
      "sources": ["03_booking_policy_faq.md > Possession", "01_mgc_aurora_heights_brochure.md > Overview"],
      "agent_instruction": "Do not state a Block B possession date. Targets are targets, not guarantees."
    },
    {
      "id": "unit_change",
      "status": "confirmed",
      "keywords": ["change unit", "switch", "swap", "different unit", "upgrade", "downgrade", "modify booking"],
      "answer": "One change to a different unit is permitted before the fourth instalment, subject to availability and payment of any price difference. No change is permitted after that.",
      "details": {},
      "sources": ["03_booking_policy_faq.md > Frequently Asked"],
      "agent_instruction": ""
    },
    {
      "id": "construction_timeline",
      "status": "partial",
      "keywords": ["construction", "timeline", "completion", "when ready", "groundbreaking", "structural", "progress", "schedule", "delivery date"],
      "answer": "Groundbreaking was November 2024. Structural completion of Block A is scheduled for Q1 2027; Block B follows two quarters later. Block A possession is targeted for Q3 2027.",
      "details": {"not_stated": "Block B possession date; current construction progress."},
      "sources": ["01_mgc_aurora_heights_brochure.md > Overview"],
      "agent_instruction": "The brochure is dated March 2025; do not claim current progress."
    },
    {
      "id": "project_overview",
      "status": "confirmed",
      "keywords": ["overview", "project", "location", "where", "address", "storey", "floors", "acres", "blocks", "about", "units"],
      "answer": "22-storey mixed-use residential tower on GT Road, Islamabad, about 4 km from Al-Jannat Mall, on 3.8 acres. 418 residential units across Block A and Block B, with a commercial podium on floors 1-3. Residential floors are therefore 4-22.",
      "details": {"unit_counts": "Studio 64 (A only), 1-Bed 96, 2-Bed Standard 128, 2-Bed Corner 42 (B only), 3-Bed Executive 66 (B only), 4-Bed Penthouse 22 (B, floors 20-22)."},
      "sources": ["01_mgc_aurora_heights_brochure.md > Overview, Unit Configuration"],
      "agent_instruction": "'Residential floors 4-22' is derived from the podium being on floors 1-3."
    },
    {
      "id": "unit_availability",
      "status": "not_stated",
      "keywords": ["available", "availability", "sold", "remaining", "inventory", "left", "stock"],
      "answer": "The brochure's 'Units available' column sums to the full 418-unit inventory, so it shows total units per type, not live availability. Live availability, specific floors and per-block split for 1-Bed and 2-Bed Standard are not in the documents.",
      "details": {},
      "sources": ["01_mgc_aurora_heights_brochure.md > Unit Configuration"],
      "agent_instruction": "Do not claim a specific unit is currently available. Refer to the sales office."
    },
    {
      "id": "margalla_view",
      "status": "ambiguous",
      "keywords": ["margalla", "view", "facing", "orientation", "hills", "mountain"],
      "answer": "All units above floor 12 in Block B face the Margalla range, and Margalla-facing carries a +6% premium. Studio and 1-Bed units are not available Margalla-facing.",
      "details": {"ambiguity": "The brochure also lists 1-Bed units in Block B, which conflicts with 'all units above floor 12 in Block B face Margalla' unless 1-Beds are only on floors 12 and below. Orientation for Block A is not stated."},
      "sources": ["01_mgc_aurora_heights_brochure.md > Unit Configuration", "02_price_list_payment_plan.md > Location Premiums"],
      "agent_instruction": "Flag the ambiguity if asked about 1-Beds or Block A views."
    },
    {
      "id": "amenities",
      "status": "confirmed",
      "keywords": ["amenities", "pool", "gym", "parking", "generator", "backup", "power", "security", "internet", "fibre", "fire", "prayer", "hall", "lounge"],
      "answer": "Rooftop infinity pool and residents' lounge (floor 22, Block A); two-level basement parking with 640 slots; 100% backup power via three 1,250 kVA generators; gymnasium, prayer area and 4,000 sq ft community hall on the podium level; 24/7 security with facial-recognition access at both tower entrances; fibre-to-the-unit internet pre-wired for two providers; central firefighting system compliant with CDA fire safety bylaws 2019.",
      "details": {"parking_note": "One parking slot per unit is mandatory and charged separately (see pricing tool)."},
      "sources": ["01_mgc_aurora_heights_brochure.md > Amenities"],
      "agent_instruction": ""
    },
    {
      "id": "approvals",
      "status": "confirmed",
      "keywords": ["approval", "approved", "cda", "noc", "legal", "epa", "environmental", "layout plan", "authority"],
      "answer": "CDA NOC reference CDA/PLW/NOC-2024/1187 dated 12 August 2024; layout plan approved 3 October 2024; Pak-EPA environmental clearance granted September 2024.",
      "details": {},
      "sources": ["01_mgc_aurora_heights_brochure.md > Approvals"],
      "agent_instruction": ""
    },
    {
      "id": "sales_office",
      "status": "confirmed",
      "keywords": ["contact", "office", "phone", "call", "visit", "hours", "open", "sales office", "number"],
      "answer": "MGC Developments Head Office, near Al-Jannat Mall, GT Road, Islamabad. Sales enquiries: 0308-77 77 275. Open Monday to Saturday, 10:00 to 19:00; closed Sundays and public holidays.",
      "details": {},
      "sources": ["01_mgc_aurora_heights_brochure.md > Sales Office"],
      "agent_instruction": ""
    },
    {
      "id": "commercial_podium",
      "status": "partial",
      "keywords": ["commercial", "shop", "shops", "podium", "retail unit", "office space", "food", "restaurant"],
      "answer": "74 commercial units (280 to 2,100 sq ft) on floors 1-3; ground floor reserved for food and beverage tenants. No anchor tenant confirmed. Residential discounts do not apply to commercial units.",
      "details": {"pricing": "Commercial prices and payment plans are not in the documents; plans are issued separately on request."},
      "sources": ["01_mgc_aurora_heights_brochure.md > Commercial Podium", "02_price_list_payment_plan.md > Discounts, Notes"],
      "agent_instruction": "Do not quote any commercial price."
    },
    {
      "id": "price_validity",
      "status": "stale_risk",
      "keywords": ["price", "prices", "current", "valid", "revision", "revised", "protected", "protection", "increase", "latest", "effective"],
      "answer": "The price list is effective 1 April 2025 and says prices are subject to revision. Bookings made before 30 June 2025 were protected against the next revision; that window has passed.",
      "details": {},
      "sources": ["02_price_list_payment_plan.md > Notes"],
      "agent_instruction": "When quoting prices, mention they come from the price list effective 1 April 2025 and should be confirmed with the sales office as they may have been revised."
    },
    {
      "id": "payment_methods",
      "status": "confirmed",
      "keywords": ["cash", "payment method", "bank transfer", "cheque", "pay", "escrow", "limit"],
      "answer": "Cash is not accepted above PKR 500,000. The token is paid into the project escrow account.",
      "details": {"ambiguity": "The price list's '12% full cash payment' discount appears to mean paying the full price upfront, not physical cash, but the documents do not define it."},
      "sources": ["03_booking_policy_faq.md > Booking Process", "02_price_list_payment_plan.md > Discounts"],
      "agent_instruction": ""
    }
  ]
}


@tool
def lookup_aurora_heights_knowledge(
    query: Optional[str] = None, 
    category: Optional[str] = None, 
    key: Optional[str] = None
) -> Union[Dict[str, Any], List[Any], str]:
    """
    Looks up information in the MGC Aurora Heights consolidated knowledge base.

    Args:
        query (Optional[str]): A keyword or phrase to search across knowledge facts 
                               (e.g. 'transfer fee', 'amenities', 'possession', 'discount').
        category (Optional[str]): Direct query into 'pricing' categories OR 'knowledge'.
                                 Valid subcategories for pricing:
                                 - 'meta', 'unit_types', 'prices', 'location_premiums',
                                   'discounts', 'payment_plan_standard', 'other_charges'.
        key (Optional[str]): A key within a pricing category (e.g. 'studio', '2bed_corner').

    Returns:
        Union[Dict[str, Any], List[Any], str]: Relevant information or error messages.
    """
    # 1. Search knowledge facts via query keyword
    if query:
        q_clean = query.lower().strip()
        matched_facts = []
        for fact in KNOWLEDGE_BASE.get("knowledge", []):
            fact_id = fact.get("id", "").lower()
            keywords = [k.lower() for k in fact.get("keywords", [])]
            answer = fact.get("answer", "").lower()
            
            if q_clean in fact_id or any(q_clean in k for k in keywords) or q_clean in answer:
                matched_facts.append(fact)
                
        if matched_facts:
            return matched_facts if len(matched_facts) > 1 else matched_facts[0]

    # 2. Category lookup for numerical/pricing data
    if category:
        pricing_data = KNOWLEDGE_BASE.get("pricing", {})
        if category in pricing_data:
            cat_data = pricing_data[category]
            if key:
                if isinstance(cat_data, dict) and key in cat_data:
                    return cat_data[key]
                elif isinstance(cat_data, list):
                    filtered = [item for item in cat_data if isinstance(item, dict) and item.get("unit_type") == key]
                    if filtered:
                        return filtered
                    return f"Error: Key '{key}' not found in list for pricing section '{category}'."
                else:
                    return f"Error: Key '{key}' not found in section '{category}'."
            return cat_data
        elif category == "knowledge":
            return KNOWLEDGE_BASE.get("knowledge", [])
        else:
            return f"Error: Category '{category}' not found. Valid pricing categories: {list(pricing_data.keys())}"

    # Default fallback
    if query:
        return f"No exact match found in knowledge base for query: '{query}'."
    
    return "Please provide either a 'query' string or a 'category' to search."





import math
from typing import Optional, Dict, Any
from langchain_core.tools import tool

# Data needed for calculation
PRICES_DATA = [
    {"unit_type": "studio", "block": "A", "price_per_sqft": 18000, "base_price": 8640000},
    {"unit_type": "1bed_standard", "block": "A", "price_per_sqft": 18500, "base_price": 13320000},
    {"unit_type": "2bed_standard", "block": "A", "price_per_sqft": 19000, "base_price": 21850000},
    {"unit_type": "1bed_standard", "block": "B", "price_per_sqft": 19000, "base_price": 13680000},
    {"unit_type": "2bed_standard", "block": "B", "price_per_sqft": 19500, "base_price": 22425000},
    {"unit_type": "2bed_corner", "block": "B", "price_per_sqft": 20500, "base_price": 26855000},
    {"unit_type": "3bed_executive", "block": "B", "price_per_sqft": 21000, "base_price": 39480000},
    {"unit_type": "4bed_penthouse", "block": "B", "price_per_sqft": 26000, "base_price": 88400000}
]

UNIT_METADATA = {
    "studio": {"margalla_eligible": False, "corner_type": False, "valid_blocks": ["A"]},
    "1bed_standard": {"margalla_eligible": False, "corner_type": False, "valid_blocks": ["A", "B"]},
    "2bed_standard": {"margalla_eligible": True, "corner_type": False, "valid_blocks": ["A", "B"]},
    "2bed_corner": {"margalla_eligible": True, "corner_type": True, "valid_blocks": ["B"]},
    "3bed_executive": {"margalla_eligible": True, "corner_type": False, "valid_blocks": ["B"]},
    "4bed_penthouse": {"margalla_eligible": True, "corner_type": False, "valid_blocks": ["B"]}
}

OTHER_CHARGES = {
    "utility_connection_per_unit": 285000,
    "parking_mandatory_one_per_unit": 1450000,
    "parking_additional_slot": 1650000,
    "maintenance_advance_months": 12,
    "maintenance_rate_per_sqft_per_month": 9.5
}


@tool
def calculate_aurora_heights_price(
    unit_type: str,
    block: str,
    floor: int,
    is_corner: bool = False,
    is_margalla_facing: bool = False,
    payment_option: str = "standard",  # Options: 'standard', 'full_payment', 'fifty_percent_upfront'
    is_overseas: bool = False,
    is_second_unit: bool = False,
    include_other_charges: bool = True
) -> Dict[str, Any]:
    """
    Calculates the detailed price, premiums, discounts, and payment schedule breakdown 
    for a unit in MGC Aurora Heights.

    Args:
        unit_type (str): Key of the unit type ('studio', '1bed_standard', '2bed_standard', 
                          '2bed_corner', '3bed_executive', '4bed_penthouse').
        block (str): 'A' or 'B'.
        floor (int): Floor number (residential floors range from 4 to 22).
        is_corner (bool): Whether the unit is a corner unit (+3% premium).
        is_margalla_facing (bool): Whether unit faces Margalla range (+6% premium).
        payment_option (str): 'standard' (0%), 'full_payment' (12% off), or 'fifty_percent_upfront' (6% off).
        is_overseas (bool): Whether buyer is an overseas Pakistani (additional +2% discount).
        is_second_unit (bool): Whether this is a second unit purchase (+1.5% discount).
        include_other_charges (bool): Whether to include parking, utilities, and advance maintenance.

    Returns:
        Dict[str, Any]: Detailed price breakdown including total cost and milestone schedule.
    """
    unit_type = unit_type.lower().strip()
    block = block.upper().strip()

    # 1. Base Price Lookup
    matched = [p for p in PRICES_DATA if p["unit_type"] == unit_type and p["block"] == block]
    if not matched:
        return {"error": f"Invalid unit_type '{unit_type}' and block '{block}' combination."}
    
    base_price = matched[0]["base_price"]
    meta = UNIT_METADATA.get(unit_type, {})

    # 2. Location Premiums (Applied on base_price, cumulative, non-discountable)
    if floor < 4 or floor > 22:
        return {"error": f"Invalid floor number {floor}. Residential floors range from 4 to 22."}

    floor_premium_pct = 0
    if 13 <= floor <= 19:
        floor_premium_pct = 4
    elif 20 <= floor <= 22:
        floor_premium_pct = 7

    corner_premium_pct = 3 if is_corner else 0
    
    # Margalla Facing check
    margalla_premium_pct = 0
    if is_margalla_facing:
        if not meta.get("margalla_eligible", False):
            return {"error": f"Unit type '{unit_type}' is not eligible for Margalla facing premium."}
        margalla_premium_pct = 6

    total_premium_pct = floor_premium_pct + corner_premium_pct + margalla_premium_pct
    total_location_premiums = (base_price * total_premium_pct) / 100

    # 3. Discounts Calculation (Applied on base_price ONLY)
    discount_pct = 0
    if payment_option == "full_payment":
        discount_pct += 12
    elif payment_option == "fifty_percent_upfront":
        discount_pct += 6
    
    if is_overseas:
        discount_pct += 2
    if is_second_unit:
        discount_pct += 1.5

    total_discounts = (base_price * discount_pct) / 100

    # Net Unit Price
    net_unit_price = base_price + total_location_premiums - total_discounts

    # 4. Mandatory Other Charges
    other_charges_breakdown = {}
    total_other_charges = 0
    if include_other_charges:
        # Approximate area based on unit metadata
        area_sqft = matched[0]["base_price"] / matched[0]["price_per_sqft"]
        advance_maint = area_sqft * OTHER_CHARGES["maintenance_rate_per_sqft_per_month"] * OTHER_CHARGES["maintenance_advance_months"]
        
        other_charges_breakdown = {
            "utility_connection": OTHER_CHARGES["utility_connection_per_unit"],
            "mandatory_parking_1_slot": OTHER_CHARGES["parking_mandatory_one_per_unit"],
            "advance_maintenance_12_months": round(advance_maint)
        }
        total_other_charges = sum(other_charges_breakdown.values())

    grand_total = net_unit_price + total_other_charges

    # 5. Milestone Breakdown (Standard Payment Plan)
    payment_schedule = {
        "booking_token_10_pct": net_unit_price * 0.10,
        "confirmation_due_within_45_days_10_pct": net_unit_price * 0.10,
        "quarterly_installment_each_3_75_pct_x16": net_unit_price * 0.0375,
        "on_possession_20_pct": net_unit_price * 0.20
    }

    return {
        "unit_details": {
            "unit_type": unit_type,
            "block": block,
            "floor": floor,
            "base_price_pkr": base_price
        },
        "premiums_pkr": {
            "floor_premium": (base_price * floor_premium_pct) / 100,
            "corner_premium": (base_price * corner_premium_pct) / 100,
            "margalla_premium": (base_price * margalla_premium_pct) / 100,
            "total_location_premiums": total_location_premiums
        },
        "discounts_pkr": {
            "discount_percentage_applied": discount_pct,
            "total_discount_amount": total_discounts
        },
        "net_unit_price_pkr": net_unit_price,
        "other_charges_pkr": {
            "breakdown": other_charges_breakdown,
            "total_other_charges": total_other_charges
        },
        "grand_total_pkr": grand_total,
        "standard_payment_schedule_pkr": payment_schedule,
        "disclaimer": "Prices are based on the April 2025 price list and subject to confirmation by MGC sales office."
    }




from tools.warranty_tools import get_warranty_claim_details_impl
from tools.service_tools import get_vehicle_service_history_impl
from tools.parts_tools import check_part_availability_impl
from tools.context_pack_tools import generate_aftermarket_context_pack_impl

if __name__ == "__main__":
    print("\n=== Warranty claim: WC1001 ===")
    print(get_warranty_claim_details_impl("WC1001"))
    print("\n=== Service history: VINDEF000123 ===")
    print(get_vehicle_service_history_impl("VINDEF000123", limit=5))
    print("\n=== Part availability: P001 / DE ===")
    print(check_part_availability_impl("P001", "DE", limit=10))
    print("\n=== Context pack: Dealer DLR003 ===")
    print(generate_aftermarket_context_pack_impl("dealer", "DLR003"))

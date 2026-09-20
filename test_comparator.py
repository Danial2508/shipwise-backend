from comparator import compare_documents


si = {
    "shipper": "APRIL FAR EAST (M) SDN BHD",
    "consignee": "EAST BRIGHT FZ-LLC",
    "notify_party": "EAST BRIGHT FZ-LLC",
    "port_of_loading": "NANTONG, CHINA (CNNTG)",
    "port_of_discharge": "KARACHI, PAKISTAN (PKKHI)",
    "container_count": "6 x 40'HC",
    "gross_weight_kg": 131058.0
}


bl = {
    "shipper": "APRIL FAR EAST (M) SDN BHD",
    "consignee": "UAB NOVAKOPA",
    "notify_party": "UAB NOVAKOPA",
    "port_of_loading": "NANTONG, CHINA (CNNTG)",
    "port_of_discharge": "KARACHI, PAKISTAN (PKKHI)",
    "container_count": "6 x 40'HC",
    "gross_weight_kg": 131058.0
}


result = compare_documents(si, bl)

print(result)
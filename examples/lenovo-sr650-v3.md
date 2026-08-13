---
card_id: "lenovo-sr650-v3#a1b2c3"
revision_id: "r1"
schema_version: "3.1.1"
review_status: active
block_reasons: []
pipeline_version: "p1"
sources: ["sha256:aaa111"]
human_notes: ""
human_approved_at: "2026-08-13"
ram_max:
  - claim_id: "a1b2c3-ram-001"
    value_raw: "Up to 8TB (32x 256GB 3DS RDIMM)"
    value_normalized: 8192
    unit: "GB"
    constraints: {cpu_count: 2, dimm_population: "32x 256GB 3DS RDIMM"}
    constraints_raw: "2x CPU, 32x 256GB 3DS RDIMM"
    measurement_basis: total
    source_id: "sha256:aaa111"
    anchor: {page: 4, fingerprint: "Memory: Up to 8TB"}
  - claim_id: "a1b2c3-ram-002"
    value_raw: "Up to 4TB"
    value_normalized: 4096
    unit: "GB"
    constraints: {cpu_count: 1}
    constraints_raw: "single-processor configurations"
    measurement_basis: total
    source_id: "sha256:aaa111"
    anchor: {page: 4, fingerprint: "single-processor"}
---
# Lenovo SR650 V3
Рендер-тело (генерируется из YAML).

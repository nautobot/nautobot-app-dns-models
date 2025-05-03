# Extending the App

Extending the application is welcome, however it is best to open an issue first, to ensure that a PR would be accepted and makes sense in terms of features and design.


# Entity Relation Diagram

```mermaid
---
Title: DNS Models Entity Relation Diagram
---
erDiagram
    DNSModel {
    }

    DNSZoneModel {
        charfield name UK
        integer ttl 
        charfied filename
        textfield description
        string soa_mname
        email soa_rname
        integer soa_refresh
        integer soa_retry
        integer soa_export
        integer soa_serial
        integer soa_minimum
    }

    DNSRecordModel {
        charfield name UK
        DNSZoneModel DNSZone
        integer ttl
        textfield description
        charfied comment
    }

    ipam_IPaddressModel {}

    ARecordModel {
        ipam_IPaddressModel IPAddress
    }

    AAAARecordModel {
        ipam_IPaddressModel IPAddress
    }

    CNAMERecordModel {
        charfied alias
    }

    MXRecordModel {
        integer preference
        charfied server
    }

    TXTRecordModel {
        textfield text
    }

    PTRRecordModel {
        charfied ptrdname
    }

    NSRecordModel {
        charfied server
    }

    SRVRecordModel {
        integer priority
        integer weight
        integer port
        charfied target
    }

    DNSModel ||--o{ DNSZoneModel : implements
    DNSModel ||--o{ DNSRecordModel : implements
    DNSRecordModel ||--o{ ARecordModel: implements
    DNSRecordModel ||--o{ AAAARecordModel: implements
    DNSRecordModel ||--o{ CNAMERecordModel: implements
    DNSRecordModel ||--o{ MXRecordModel: implements
    DNSRecordModel ||--o{ TXTRecordModel: implements
    DNSRecordModel ||--o{ PTRRecordModel: implements
    DNSRecordModel ||--o{ NSRecordModel: implements
    DNSRecordModel ||--o{ SRVRecordModel: implements

    DNSRecordModel ||--o{ DNSZoneModel: "is inside of a"

    ARecordModel ||--|| ipam_IPaddressModel: "references"
    AAAARecordModel ||--|| ipam_IPaddressModel: "references"
```

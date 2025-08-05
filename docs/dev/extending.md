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

    DNSRecord {
        charfield name UK
        DNSZoneModel DNSZone
        integer ttl
        textfield description
        charfied comment
    }

    ipam_IPaddressModel {}

    ARecord {
        ipam_IPaddressModel IPAddress
    }

    AAAARecord {
        ipam_IPaddressModel IPAddress
    }

    CNAMERecord {
        charfied alias
    }

    MXRecord {
        integer preference
        charfied server
    }

    TXTRecord {
        textfield text
    }

    PTRRecord {
        charfied ptrdname
    }

    NSRecord {
        charfied server
    }

    SRVRecord {
        integer priority
        integer weight
        integer port
        charfied target
    }

    DNSModel ||--o{ DNSZoneModel : implements
    DNSModel ||--o{ DNSRecord : implements
    DNSRecord ||--o{ ARecord: implements
    DNSRecord ||--o{ AAAARecord: implements
    DNSRecord ||--o{ CNAMERecord: implements
    DNSRecord ||--o{ MXRecord: implements
    DNSRecord ||--o{ TXTRecord: implements
    DNSRecord ||--o{ PTRRecord: implements
    DNSRecord ||--o{ NSRecord: implements
    DNSRecord ||--o{ SRVRecord: implements

    DNSRecord ||--o{ DNSZoneModel: "is inside of a"

    ARecord ||--|| ipam_IPaddressModel: "references"
    AAAARecord ||--|| ipam_IPaddressModel: "references"
```

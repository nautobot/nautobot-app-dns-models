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

    DNSView {
        charfield name UK
        textfield description
    }

    ipam_PrefixModel {}

    DNSViewPrefixAssignment {
        DNSView dns_view FK
        ipam_PrefixModel prefix FK
    }

    DNSRegistrar {
        charfield name UK
        url url
        charfield account_number
    }

    extras_StatusModel {}

    DNSRegistration {
        DNSRegistrar dns_registrar FK
        DNSZone dns_zone FK
        extras_StatusModel status FK
        datefield expiration_date
        boolean auto_renewal
        boolean registry_locked
        boolean transfer_locked
        boolean privacy_enabled
        boolean website_forwarding_enabled
        integer renewal_term_months
        boolean dnssec_enabled
    }

    tenancy_TenantModel {}

    DNSZone {
        charfield name UK
        DNSView dns_view FK
        integer ttl
        charfield filename
        textfield description
        string soa_mname
        email soa_rname
        integer soa_refresh
        integer soa_retry
        integer soa_expire
        integer soa_serial
        integer soa_minimum
        tenancy_TenantModel tenant FK
        boolean auto_create_ptr
    }

    DNSRecord {
        charfield name UK
        DNSZone zone FK
        integer ttl
        textfield description
        charfield comment
    }

    ipam_IPaddressModel {}

    ARecord {
        ipam_IPaddressModel ip_address FK
    }

    AAAARecord {
        ipam_IPaddressModel ip_address FK
    }

    CNAMERecord {
        charfield alias
    }

    MXRecord {
        integer preference
        charfield mail_server
    }

    TXTRecord {
        charfield text
    }

    PTRRecord {
        charfield ptrdname
    }

    NSRecord {
        charfield server
    }

    SRVRecord {
        integer priority
        integer weight
        integer port
        charfield target
    }

    DNSModel ||--o{ DNSZone : implements
    DNSModel ||--o{ DNSRecord : implements
    DNSRecord ||--o{ ARecord: implements
    DNSRecord ||--o{ AAAARecord: implements
    DNSRecord ||--o{ CNAMERecord: implements
    DNSRecord ||--o{ MXRecord: implements
    DNSRecord ||--o{ TXTRecord: implements
    DNSRecord ||--o{ PTRRecord: implements
    DNSRecord ||--o{ NSRecord: implements
    DNSRecord ||--o{ SRVRecord: implements

    DNSZone ||--o{ DNSRecord: "contains"
    DNSZone }o--|| DNSView: "belongs to"
    DNSZone }o--o| tenancy_TenantModel: "belongs to"

    DNSView ||--o{ DNSViewPrefixAssignment: "assigns"
    ipam_PrefixModel ||--o{ DNSViewPrefixAssignment: "assigned via"

    DNSRegistration }o--|| DNSRegistrar: "registered with"
    DNSRegistration }o--|| DNSZone: "registers"
    DNSRegistration }o--|| extras_StatusModel: "has status"

    ARecord }o--|| ipam_IPaddressModel: "references"
    AAAARecord }o--|| ipam_IPaddressModel: "references"

    ARecord ||..o{ PTRRecord: "auto-creates (when zone.auto_create_ptr)"
    AAAARecord ||..o{ PTRRecord: "auto-creates (when zone.auto_create_ptr)"
```

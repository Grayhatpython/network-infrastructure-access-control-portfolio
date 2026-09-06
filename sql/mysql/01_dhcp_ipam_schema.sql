-- DHCP/IPAM schema - portfolio snapshot

CREATE TABLE dhcp_scope
(
    scope_id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
    vlan_tag                SMALLINT UNSIGNED NOT NULL,
    scope_name              VARCHAR(100) NOT NULL,
    network_address         VARCHAR(45) NOT NULL,
    subnet_mask             VARCHAR(45) NOT NULL,
    broadcast_address       VARCHAR(45) NOT NULL,
    gateway_address         VARCHAR(45) NOT NULL,
    domain_name             VARCHAR(255) NULL,
    dns_servers             VARCHAR(255) NULL,
    default_lease_seconds   INT UNSIGNED NOT NULL DEFAULT 1800,
    max_lease_seconds       INT UNSIGNED NOT NULL DEFAULT 3600,
    enabled                 TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (scope_id),
    UNIQUE KEY uq_dhcp_scope_vlan (vlan_tag)
);

CREATE TABLE dhcp_ip_pool
(
    ip_id       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    scope_id    INT UNSIGNED NOT NULL,
    ip_address  VARCHAR(45) NOT NULL,
    pool_state  ENUM('DYNAMIC', 'RESERVED', 'EXCLUDED')
                NOT NULL DEFAULT 'DYNAMIC',
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (ip_id),
    UNIQUE KEY uq_scope_ip (scope_id, ip_address),
    CONSTRAINT fk_pool_scope
        FOREIGN KEY (scope_id) REFERENCES dhcp_scope(scope_id)
);

CREATE TABLE network_lease_log
(
    log_id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    client_mac    CHAR(17) NOT NULL,
    assigned_ip   VARCHAR(45) NOT NULL,
    vlan_tag      SMALLINT UNSIGNED NOT NULL,
    client_host   VARCHAR(253) NULL,
    dhcp_message  TEXT NOT NULL,
    logged_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (log_id),
    INDEX idx_lease_mac (client_mac),
    INDEX idx_lease_ip (assigned_ip),
    INDEX idx_lease_time (logged_at)
);

CREATE TABLE dhcp_reservation
(
    reservation_id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    scope_id            INT UNSIGNED NOT NULL,
    client_mac          CHAR(17) NOT NULL,
    reserved_ip         VARCHAR(45) NOT NULL,
    client_host         VARCHAR(253) NULL,
    first_log_id        BIGINT UNSIGNED NULL,
    reservation_source  VARCHAR(32) NOT NULL DEFAULT 'AUTO_FIRST_LEASE',
    enabled             TINYINT(1) NOT NULL DEFAULT 1,
    apply_state         ENUM('PENDING', 'APPLIED') NOT NULL DEFAULT 'PENDING',
    applied_at          TIMESTAMP NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (reservation_id),
    UNIQUE KEY uk_scope_mac (scope_id, client_mac),
    UNIQUE KEY uk_scope_reserved_ip (scope_id, reserved_ip),
    CONSTRAINT fk_reservation_scope
        FOREIGN KEY (scope_id) REFERENCES dhcp_scope(scope_id)
);

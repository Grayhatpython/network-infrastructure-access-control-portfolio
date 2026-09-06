-- Core lifecycle trigger used in the current lab.
-- Full DHCPACK parsing trigger is documented separately because
-- its parser depends on the exact rsyslog message format.

DELIMITER //

CREATE TRIGGER trg_dhcp_reservation_after_delete_release_pool
AFTER DELETE ON dhcp_reservation
FOR EACH ROW
BEGIN
    UPDATE dhcp_ip_pool
       SET pool_state = 'DYNAMIC'
     WHERE scope_id = OLD.scope_id
       AND ip_address = OLD.reserved_ip
       AND pool_state = 'RESERVED';
END//

DELIMITER ;

-- DHCPACK ingestion flow used in the lab:
--
-- Syslog.SystemEvents
--   -> trg_systemevents_after_insert
--   -> network_lease_log
--   -> reservation trigger
--   -> dhcp_reservation
--   -> dhcp_ip_pool RESERVED
--
-- The public repo intentionally avoids hard-coding parser logic until
-- sample log formats are fully sanitized and documented.

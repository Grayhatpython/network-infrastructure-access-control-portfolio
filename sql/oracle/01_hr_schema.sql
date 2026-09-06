-- Oracle HR schema - public example
-- Secrets/passwords are intentionally omitted.

CREATE TABLE department
(
    dept_code   VARCHAR2(10)  NOT NULL,
    dept_name   VARCHAR2(100) NOT NULL,
    enabled     CHAR(1) DEFAULT 'Y' NOT NULL,
    created_at  TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,

    CONSTRAINT pk_department PRIMARY KEY (dept_code),
    CONSTRAINT ck_department_enabled CHECK (enabled IN ('Y', 'N'))
);

CREATE TABLE employee
(
    emp_id            VARCHAR2(64)  NOT NULL,
    emp_name          VARCHAR2(100) NOT NULL,
    nt_password_hash  VARCHAR2(32)  NOT NULL,
    dept_code         VARCHAR2(10)  NOT NULL,
    active_yn         CHAR(1) DEFAULT 'Y' NOT NULL,
    created_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at        TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,

    CONSTRAINT pk_employee PRIMARY KEY (emp_id),
    CONSTRAINT fk_employee_department
        FOREIGN KEY (dept_code) REFERENCES department(dept_code),
    CONSTRAINT ck_employee_active CHECK (active_yn IN ('Y', 'N')),
    CONSTRAINT ck_employee_nt_hash CHECK (LENGTH(nt_password_hash) = 32)
);

CREATE OR REPLACE TRIGGER trg_employee_updated_at
BEFORE UPDATE ON employee
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE VIEW v_radius_account AS
SELECT
    e.emp_id,
    e.emp_name,
    e.nt_password_hash,
    e.dept_code,
    e.active_yn,
    e.updated_at
FROM employee e
JOIN department d
  ON d.dept_code = e.dept_code
WHERE d.enabled = 'Y';

-- Example:
-- GRANT SELECT ON v_radius_account TO RADIUS_SYNC;

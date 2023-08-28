DROP TABLE IF EXISTS probii CASCADE;
CREATE TABLE probii (
	probius_id UUID NOT NULL,
	creator_id UUID NOT NULL,
	default_plastic_id TEXT DEFAULT '',
	project_id UUID,
	stripe_customer_id TEXT DEFAULT '',

	credit INT DEFAULT 0,
	debt INT DEFAULT 0,
	is_autopay_enabled BOOL DEFAULT false,
	first_period INT NOT NULL,
	is_bill_overdue BOOL DEFAULT false,
	is_closed BOOL DEFAULT false,
	is_in_arrears BOOL DEFAULT false,
	notes TEXT DEFAULT '',
	time_last_bill_issued BIGINT DEFAULT 0,
	time_last_paid_off BIGINT DEFAULT 0,
	tokens_bought INT DEFAULT 0,
	tokens_used INT DEFAULT 0,

	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (probius_id)
);


DROP TABLE IF EXISTS charges CASCADE;
CREATE TABLE charges (
	charge_id UUID NOT NULL,
	probius_id UUID,
	charge_type INT NOT NULL,
	currency TEXT DEFAULT 'USD',
	description TEXT DEFAULT '',
	meta TEXT DEFAULT '',
	period INT NOT NULL,
	plan_id TEXT,
	price INT NOT NULL,
	units INT NOT NULL,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (charge_id)
	-- CONSTRAINT fk_charges_challenge_id
		-- FOREIGN KEY (challenge_id)
		-- REFERENCES challenges(challenge_id)
);
CREATE INDEX idx_charges_probius_id_and_period ON 
	charges(probius_id, period);


-- payment_platform: btcpay, stripe
-- payment_purpose: credit, credit_back, overage, period
DROP TABLE IF EXISTS payments CASCADE;
CREATE TABLE payments (
	payment_id UUID NOT NULL,
	bill_id UUID,
	probius_id UUID NOT NULL,
	btcpay_invoice_id TEXT,
	payment_intent_id TEXT,
	payment_platform INT NOT NULL,
	stripe_invoice_id TEXT,
	-- eveything else mirrors stripe_payment_attempts
	admin_notes TEXT,
	basket_string TEXT NOT NULL,
	credit_applied INT NOT NULL,
	currency TEXT DEFAULT 'USD',
	is_autopay_selected BOOL NOT NULL,
	notes TEXT,
	plastic_id TEXT,
	silo TEXT NOT NULL,
	status INT NOT NULL,
	terms_accepted_version TEXT NOT NULL,
	total_price INT NOT NULL,
	total_price_after_credit INT NOT NULL,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (payment_id),
	CONSTRAINT fk_payments_probius_id
		FOREIGN KEY (probius_id)
		REFERENCES probii(probius_id)
);
CREATE INDEX idx_payments_probius_id ON 
	payments(probius_id);


DROP TABLE IF EXISTS stripe_payment_attempts CASCADE;
CREATE TABLE stripe_payment_attempts (
	attempt_id UUID NOT NULL,
	bill_id UUID,
	plan_id TEXT,
	plastic_id TEXT NOT NULL,
	probius_id UUID NOT NULL,
	project_id UUID,

	payment_intent_id TEXT,
	admin_notes TEXT DEFAULT '',
	basket_string TEXT NOT NULL,
	credit_applied INT NOT NULL,
	currency TEXT DEFAULT 'USD',
	is_autopay_selected BOOL NOT NULL,
	silo TEXT NOT NULL,
	status INT NOT NULL,
	terms_accepted_version TEXT NOT NULL,
	total_price INT NOT NULL,
	total_price_after_credit INT NOT NULL,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (attempt_id),
	CONSTRAINT fk_stripe_payment_attempts_probius_id
		FOREIGN KEY (probius_id)
		REFERENCES probii(probius_id)
);
CREATE INDEX idx_stripe_payment_attempts_status ON 
	stripe_payment_attempts(status);


DROP TABLE IF EXISTS agreement_accepted_logs CASCADE;
CREATE TABLE agreement_accepted_logs (
	developer_id UUID NOT NULL,
	probius_id UUID NOT NULL,
	is_accepted BOOL NOT NULL,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (developer_id, time_created)
);


DROP TABLE IF EXISTS bills CASCADE;
CREATE TABLE bills (
	bill_id UUID NOT NULL,
	admin_notes TEXT,
	bill_type TEXT NOT NULL,
	charge_ids TEXT DEFAULT '[]',
	credit_applied INT DEFAULT 0,
	credit_overflow INT DEFAULT 0,
	currency TEXT DEFAULT 'USD',
	notes TEXT DEFAULT '',
	period INT NOT NULL,
	price INT NOT NULL,
	probius_id UUID NOT NULL,
	status TEXT NOT NULL,
	was_autopay_used BOOL DEFAULT FALSE,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (bill_id),
	CONSTRAINT fk_monthly_bills_probius_id
		FOREIGN KEY (probius_id)
		REFERENCES probii(probius_id)
);

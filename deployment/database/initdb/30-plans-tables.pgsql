-- we can create a plan_demuxer table to lookup copies of a plan
-- rules: semi-colon separated list of rules
-- plan types: small, medium, large, custom
DROP TABLE IF EXISTS plans CASCADE;
CREATE TABLE plans (
	plan_id TEXT NOT NULL UNIQUE,
	sort_id INT NOT NULL,

	bundled_tokens INT NOT NULL,
	months INT DEFAULT 12,
	price INT NOT NULL,
	price_currency TEXT NOT NULL,

	admin_notes TEXT NOT NULL,
	description TEXT NOT NULL,
	is_available BOOL NOT NULL,
	is_tailored BOOL NOT NULL DEFAULT false,
	rules TEXT NOT NULL,
	title TEXT NOT NULL,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (plan_id)
);

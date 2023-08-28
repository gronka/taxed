DROP TABLE IF EXISTS properties CASCADE;
CREATE TABLE properties (
	property_id UUID NOT NULL UNIQUE,
	surfer_id UUID NOT NULL,

	category TEXT DEFAULT '',
	notes TEXT DEFAULT '',

	address TEXT DEFAULT '',
	street_1 TEXT DEFAULT '',
	street_2 TEXT DEFAULT '',
	city TEXT DEFAULT '',
	state TEXT DEFAULT '',
	county TEXT DEFAULT '',
	country TEXT DEFAULT '',
	postal TEXT DEFAULT '',

	time_purchased BIGINT DEFAULT 0,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (property_id)
);
CREATE INDEX idx_properties_surfer_id ON properties(surfer_id);
-- CREATE INDEX idx_properties_challenge_id ON properties(challenge_id);

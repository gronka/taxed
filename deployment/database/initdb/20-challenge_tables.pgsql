DROP TABLE IF EXISTS challenges CASCADE;
CREATE TABLE challenges (
	challenge_id UUID NOT NULL UNIQUE,
	surfer_id UUID,
	target_property_id UUID,

	-- from v1 - might be useful?
	-- reason_appraised TEXT,
	-- reason_business TEXT,
	-- reason_defects TEXT,
	-- reason_description TEXT,
	-- reason_improvements TEXT,
	-- reason_new_buy TEXT,
	-- reason_occupy TEXT,
	-- reason_portion TEXT,
	-- reason_purchase_price TEXT,
	-- reason_recent_offer TEXT,
	-- reason_string TEXT,
	-- hearing TEXT,

	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (challenge_id)
);
CREATE INDEX idx_challenges_surfer_id ON challenges(surfer_id);


DROP TABLE IF EXISTS comparables CASCADE;
CREATE TABLE comparables (
	comparable_id UUID NOT NULL UNIQUE,
	challenge_id UUID NOT NULL,
	property_id UUID,
	target_property_id UUID NOT NULL,

	query_url TEXT DEFAULT '',
	query_source TEXT DEFAULT '',
	-- true if data from Attom is missing a value
	is_data_damaged BOOLEAN DEFAULT FALSE,
	marker_label TEXT DEFAULT '',

	mortgage_holder TEXT DEFAULT '',
	parcel_id TEXT DEFAULT '',
	miles TEXT DEFAULT '',
	sqft_living TEXT DEFAULT '',
	sqft_lot TEXT DEFAULT '',
	latitude TEXT DEFAULT '',
	longitude TEXT DEFAULT '',
	sale_date TEXT DEFAULT '',
	sale_price TEXT DEFAULT '',
	year_built TEXT DEFAULT '',
	bath_count TEXT DEFAULT '',
	bed_count TEXT DEFAULT '',
	assessed_price_1 TEXT DEFAULT '',
	assessed_price_2 TEXT DEFAULT '',

	street_1 TEXT DEFAULT '',
	city TEXT DEFAULT '',
	state TEXT DEFAULT '',
	postal TEXT DEFAULT '',

	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (comparable_id)
);
CREATE INDEX idx_comparables_property_id ON comparables(property_id);
CREATE INDEX idx_comparables_challenge_id ON comparables(challenge_id);

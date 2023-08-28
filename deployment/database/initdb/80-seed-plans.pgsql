-- free
INSERT INTO plans (
	plan_id,
	sort_id,
	admin_notes,
	description,
	is_available,
	is_tailored,
	title,
	price,
	price_currency,
	months,
	bundled_tokens,
	rules,
	time_created, 
	time_updated) VALUES (
	'free', -- plan_id
	99, --sort_id
	'', -- admin_notes
	'No benefits: you must purchase a plan to access Fairly Taxed services.', -- description
	true, -- is_available
	false, -- is_tailored
	'No plan', -- title
	0, -- price
	'USD', -- currency
	0, -- months
	0, -- bundled_tokens
	'', -- rules
	1635357669,
	1635357669);

-- small
INSERT INTO plans (
	plan_id,
	sort_id,
	admin_notes,
	description,
	is_available,
	is_tailored,
	title,
	price,
	price_currency,
	months,
	bundled_tokens,
	rules,
	time_created, 
	time_updated) VALUES (
	'small', -- plan_id
	0, --sort_id
	'', -- admin_notes
	'For homeowners. Subscribe for 3 years and receive 3 tax challenge tokens.', -- description
	true, -- is_available
	false, -- is_tailored
	'Residential', -- title
	10500, -- price
	'USD', -- currency
	36, -- months
	3, -- bundled_tokens
	'', -- rules
	1635357669,
	1635357669);

-- medium
INSERT INTO plans (
	plan_id,
	sort_id,
	admin_notes,
	description,
	is_available,
	is_tailored,
	title,
	price,
	price_currency,
	months,
	bundled_tokens,
	rules,
	time_created, 
	time_updated) VALUES (
	'medium', -- plan_id
	10, --sort_id
	'', -- admin_notes
	'For real estate agents. Annual subscription with a small fee for each token.', -- description
	true, -- is_available
	false, -- is_tailored
	'Investor', -- title
	5000, -- price
	'USD', -- currency
	12, -- months
	0, -- bundled_tokens
	'', -- rules
	1635357669,
	1635357669);

-- large
INSERT INTO plans (
	plan_id,
	sort_id,
	admin_notes,
	description,
	is_available,
	is_tailored,
	title,
	price,
	price_currency,
	months,
	bundled_tokens,
	rules,
	time_created, 
	time_updated) VALUES (
	'large', -- plan_id
	20, --sort_id
	'', -- admin_notes
	'For institutional investors. Annual subscription with unlimited challenge tokens for free.', -- description
	true, -- is_available
	false, -- is_tailored
	'Institutional', -- title
	100000, -- price
	'USD', -- currency
	12, -- months
	0, -- bundled_tokens
	'', -- rules
	1635357669,
	1635357669);

-- contact
INSERT INTO plans (
	plan_id,
	sort_id,
	admin_notes,
	description,
	is_available,
	is_tailored,
	title,
	price,
	price_currency,
	months,
	bundled_tokens,
	rules,
	time_created, 
	time_updated) VALUES (
	'contact', -- plan_id
	30, --sort_id
	'', -- admin_notes
	'Contact us to tailor a plan to your needs with 24/7 support: tyler@fairlytaxed.com', -- description
	true, -- is_available
	false, -- is_tailored
	'Enterprise Support Plan', -- title
	0, -- price
	'USD', -- currency
	0, -- months
	0, -- bundled_tokens
	'', -- rules
	1635357669,
	1635357669);

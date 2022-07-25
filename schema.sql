Create table brewery (
	brewery_id INT Primary Key,
	brewery_name varchar(100),
	city varchar(100),
	state varchar(100),
	address varchar (100),
	zip varchar(100),
	country varchar(100),
	lat float,
	lon float
);

Create table beer_review (
	brewery_id INT,
	Foreign Key(brewery_id) References brewery(brewery_id),
	brewery_name varchar(100),
	beer_style varchar(100),
	beer_name varchar(100),
	beer_id float,
	review_overall float
);
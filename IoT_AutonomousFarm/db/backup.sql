--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Debian 17.5-1.pgdg120+1)
-- Dumped by pg_dump version 17.5 (Debian 17.5-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: area_plants; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.area_plants (
    area_id integer NOT NULL,
    plant_id integer NOT NULL,
    greenhouse_id integer
);


ALTER TABLE public.area_plants OWNER TO iotproject;

--
-- Name: areas; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.areas (
    area_id integer NOT NULL,
    name character varying(100) NOT NULL,
    greenhouse_id integer NOT NULL
);


ALTER TABLE public.areas OWNER TO iotproject;

--
-- Name: areas_area_id_seq; Type: SEQUENCE; Schema: public; Owner: iotproject
--

CREATE SEQUENCE public.areas_area_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.areas_area_id_seq OWNER TO iotproject;

--
-- Name: areas_area_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iotproject
--

ALTER SEQUENCE public.areas_area_id_seq OWNED BY public.areas.area_id;


--
-- Name: availabledevices; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.availabledevices (
    device_id integer NOT NULL,
    name character varying(100) NOT NULL,
    type character varying(100) NOT NULL,
    configuration jsonb
);


ALTER TABLE public.availabledevices OWNER TO iotproject;

--
-- Name: availabledevices_device_id_seq; Type: SEQUENCE; Schema: public; Owner: iotproject
--

CREATE SEQUENCE public.availabledevices_device_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.availabledevices_device_id_seq OWNER TO iotproject;

--
-- Name: availabledevices_device_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iotproject
--

ALTER SEQUENCE public.availabledevices_device_id_seq OWNED BY public.availabledevices.device_id;


--
-- Name: availablesensors; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.availablesensors (
    sensor_id integer NOT NULL,
    name character varying(100) NOT NULL,
    type character varying(50) NOT NULL,
    unit character varying(50),
    threshold_range jsonb,
    domain jsonb
);


ALTER TABLE public.availablesensors OWNER TO iotproject;

--
-- Name: availablesensors_sensor_id_seq; Type: SEQUENCE; Schema: public; Owner: iotproject
--

CREATE SEQUENCE public.availablesensors_sensor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.availablesensors_sensor_id_seq OWNER TO iotproject;

--
-- Name: availablesensors_sensor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iotproject
--

ALTER SEQUENCE public.availablesensors_sensor_id_seq OWNED BY public.availablesensors.sensor_id;


--
-- Name: devices; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.devices (
    device_id integer NOT NULL,
    greenhouse_id integer NOT NULL,
    name character varying(100) NOT NULL,
    type character varying(100) NOT NULL,
    CONSTRAINT device_name_check CHECK (((name)::text = ANY (ARRAY[('DeviceConnector'::character varying)::text, ('HumidityManagement'::character varying)::text, ('LightManagement'::character varying)::text, ('NutrientManagement'::character varying)::text, ('DataAnalysis'::character varying)::text, ('TimeShift'::character varying)::text, ('ThingSpeakAdaptor'::character varying)::text, ('TelegramBot'::character varying)::text, ('WebApp'::character varying)::text]))),
    CONSTRAINT device_type_check CHECK (((type)::text = ANY (ARRAY[('DeviceConnector'::character varying)::text, ('Microservices'::character varying)::text, ('UI'::character varying)::text, ('ThingSpeakAdaptor'::character varying)::text])))
);


ALTER TABLE public.devices OWNER TO iotproject;

--
-- Name: devices_device_id_seq; Type: SEQUENCE; Schema: public; Owner: iotproject
--

CREATE SEQUENCE public.devices_device_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.devices_device_id_seq OWNER TO iotproject;

--
-- Name: devices_device_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iotproject
--

ALTER SEQUENCE public.devices_device_id_seq OWNED BY public.devices.device_id;


--
-- Name: greenhouses; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.greenhouses (
    greenhouse_id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying(100) NOT NULL,
    location character varying(255),
    thingspeak_config jsonb
);


ALTER TABLE public.greenhouses OWNER TO iotproject;

--
-- Name: greenhouses_greenhouse_id_seq; Type: SEQUENCE; Schema: public; Owner: iotproject
--

CREATE SEQUENCE public.greenhouses_greenhouse_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.greenhouses_greenhouse_id_seq OWNER TO iotproject;

--
-- Name: greenhouses_greenhouse_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iotproject
--

ALTER SEQUENCE public.greenhouses_greenhouse_id_seq OWNED BY public.greenhouses.greenhouse_id;


--
-- Name: otps; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.otps (
    telegram_user_id bigint NOT NULL,
    otp character(6) NOT NULL
);


ALTER TABLE public.otps OWNER TO iotproject;

--
-- Name: plants; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.plants (
    plant_id integer NOT NULL,
    name character varying(100) NOT NULL,
    species character varying(100) NOT NULL,
    desired_thresholds jsonb
);


ALTER TABLE public.plants OWNER TO iotproject;

--
-- Name: plants_plant_id_seq; Type: SEQUENCE; Schema: public; Owner: iotproject
--

CREATE SEQUENCE public.plants_plant_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.plants_plant_id_seq OWNER TO iotproject;

--
-- Name: plants_plant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iotproject
--

ALTER SEQUENCE public.plants_plant_id_seq OWNED BY public.plants.plant_id;


--
-- Name: scheduled_events; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.scheduled_events (
    event_id integer NOT NULL,
    frequency character varying(50) NOT NULL,
    execution_time timestamp without time zone NOT NULL,
    sensor_id integer NOT NULL,
    greenhouse_id integer NOT NULL,
    parameter character varying(20) NOT NULL,
    value numeric(10,2) NOT NULL,
    CONSTRAINT frequency_values CHECK (((frequency)::text = ANY (ARRAY[('Once'::character varying)::text, ('Daily'::character varying)::text, ('Weekly'::character varying)::text, ('Monthly'::character varying)::text]))),
    CONSTRAINT scheduled_events_parameter_check CHECK (((parameter)::text = ANY ((ARRAY['Temperature'::character varying, 'Humidity'::character varying, 'SoilMoisture'::character varying, 'pH'::character varying, 'Nitrogen'::character varying, 'Phosphorus'::character varying, 'Potassium'::character varying, 'LightIntensity'::character varying])::text[])))
);


ALTER TABLE public.scheduled_events OWNER TO iotproject;

--
-- Name: scheduled_events_event_id_seq; Type: SEQUENCE; Schema: public; Owner: iotproject
--

CREATE SEQUENCE public.scheduled_events_event_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scheduled_events_event_id_seq OWNER TO iotproject;

--
-- Name: scheduled_events_event_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iotproject
--

ALTER SEQUENCE public.scheduled_events_event_id_seq OWNED BY public.scheduled_events.event_id;


--
-- Name: sensors; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.sensors (
    sensor_id integer NOT NULL,
    area_id integer NOT NULL,
    type character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    unit character varying(10) NOT NULL,
    threshold_range jsonb NOT NULL,
    domain jsonb NOT NULL,
    greenhouse_id integer,
    CONSTRAINT check_sensor_type CHECK (((type)::text = ANY (ARRAY[('Temperature'::character varying)::text, ('Humidity'::character varying)::text, ('SoilMoisture'::character varying)::text, ('LightIntensity'::character varying)::text, ('pH'::character varying)::text, ('NPK'::character varying)::text])))
);


ALTER TABLE public.sensors OWNER TO iotproject;

--
-- Name: sensors_sensor_id_seq; Type: SEQUENCE; Schema: public; Owner: iotproject
--

CREATE SEQUENCE public.sensors_sensor_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sensors_sensor_id_seq OWNER TO iotproject;

--
-- Name: sensors_sensor_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iotproject
--

ALTER SEQUENCE public.sensors_sensor_id_seq OWNED BY public.sensors.sensor_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    username character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash bytea,
    telegram_user_id bigint
);


ALTER TABLE public.users OWNER TO iotproject;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: iotproject
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO iotproject;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iotproject
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: areas area_id; Type: DEFAULT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.areas ALTER COLUMN area_id SET DEFAULT nextval('public.areas_area_id_seq'::regclass);


--
-- Name: availabledevices device_id; Type: DEFAULT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.availabledevices ALTER COLUMN device_id SET DEFAULT nextval('public.availabledevices_device_id_seq'::regclass);


--
-- Name: availablesensors sensor_id; Type: DEFAULT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.availablesensors ALTER COLUMN sensor_id SET DEFAULT nextval('public.availablesensors_sensor_id_seq'::regclass);


--
-- Name: devices device_id; Type: DEFAULT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.devices ALTER COLUMN device_id SET DEFAULT nextval('public.devices_device_id_seq'::regclass);


--
-- Name: greenhouses greenhouse_id; Type: DEFAULT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.greenhouses ALTER COLUMN greenhouse_id SET DEFAULT nextval('public.greenhouses_greenhouse_id_seq'::regclass);


--
-- Name: plants plant_id; Type: DEFAULT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.plants ALTER COLUMN plant_id SET DEFAULT nextval('public.plants_plant_id_seq'::regclass);


--
-- Name: scheduled_events event_id; Type: DEFAULT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.scheduled_events ALTER COLUMN event_id SET DEFAULT nextval('public.scheduled_events_event_id_seq'::regclass);


--
-- Name: sensors sensor_id; Type: DEFAULT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.sensors ALTER COLUMN sensor_id SET DEFAULT nextval('public.sensors_sensor_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Data for Name: area_plants; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.area_plants (area_id, plant_id, greenhouse_id) FROM stdin;
\.


--
-- Data for Name: areas; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.areas (area_id, name, greenhouse_id) FROM stdin;
22	Main Area	28
23	North Area	28
\.


--
-- Data for Name: availabledevices; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.availabledevices (device_id, name, type, configuration) FROM stdin;
1	DataAnalysis	Microservices	{"N": 10}
2	ThingSpeakAdaptor	ThingSpeakAdaptor	\N
3	TimeShift	Microservices	\N
4	NutrientManagement	Microservices	\N
5	DeviceConnector	DeviceConnector	\N
6	LightManagement	Microservices	\N
7	TelegramBot	UI	\N
8	WebApp	UI	\N
9	HumidityManagement	Microservices	\N
\.


--
-- Data for Name: availablesensors; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.availablesensors (sensor_id, name, type, unit, threshold_range, domain) FROM stdin;
1	Temperature Sensor	Temperature	°C	{"max": 50, "min": -10}	{"max": 100, "min": -50}
2	Humidity Sensor	Humidity	%	{"max": 70, "min": 30}	{"max": 100, "min": 0}
3	NPK Sensor	NPK	mg/kg	{"K": {"max": 400, "min": 100}, "N": {"max": 150, "min": 50}, "P": {"max": 300, "min": 75}}	{"max": 1000, "min": 0}
4	Soil Moisture Sensor	SoilMoisture	%	{"max": 80, "min": 20}	{"max": 100, "min": 0}
5	pH Sensor	pH	pH	{"max": 7.5, "min": 6.0}	{"max": 10.0, "min": 3.0}
6	Light Intensity Sensor	LightIntensity	lux	{"max": 800, "min": 400}	{"max": 2000, "min": 0}
\.


--
-- Data for Name: devices; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.devices (device_id, greenhouse_id, name, type) FROM stdin;
76	28	DeviceConnector	DeviceConnector
77	28	HumidityManagement	Microservices
78	28	LightManagement	Microservices
79	28	NutrientManagement	Microservices
80	28	DataAnalysis	Microservices
81	28	TimeShift	Microservices
82	28	ThingSpeakAdaptor	ThingSpeakAdaptor
83	28	TelegramBot	UI
\.


--
-- Data for Name: greenhouses; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.greenhouses (greenhouse_id, user_id, name, location, thingspeak_config) FROM stdin;
28	0	MyGreenhouse	Torino	{"read_key": "ZPZG4DZDXG31P2FU", "write_key": "B1VQS0V9EO4UZFXB", "channel_id": "3002703"}
\.


--
-- Data for Name: otps; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.otps (telegram_user_id, otp) FROM stdin;
\.


--
-- Data for Name: plants; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.plants (plant_id, name, species, desired_thresholds) FROM stdin;
0	Tomato	Solanum lycopersicum	{"pH": {"max": 6.8, "min": 5.5}, "NPK": {"K": {"max": 400.0, "min": 100.0}, "N": {"max": 150.0, "min": 50.0}, "P": {"max": 200.0, "min": 100.0}}, "Humidity": {"max": 70.0, "min": 50.0}, "Temperature": {"max": 26.0, "min": 18.0}, "SoilMoisture": {"max": 70.0, "min": 60.0}, "LightIntensity": {"max": 800.0, "min": 200.0}}
2	Bell Pepper	Capsicum annuum	{"pH": {"max": 6.8, "min": 6.0}, "NPK": {"K": {"max": 350.0, "min": 100.0}, "N": {"max": 150.0, "min": 50.0}, "P": {"max": 300.0, "min": 100.0}}, "Humidity": {"max": 75.0, "min": 60.0}, "Temperature": {"max": 30.0, "min": 18.0}, "SoilMoisture": {"max": 70.0, "min": 60.0}, "LightIntensity": {"max": 800.0, "min": 200.0}}
1	Zucchini	Cucurbita pepo	{"pH": {"max": 6.8, "min": 6.0}, "NPK": {"K": {"max": 350.0, "min": 100.0}, "N": {"max": 250.0, "min": 100.0}, "P": {"max": 300.0, "min": 100.0}}, "Humidity": {"max": 80.0, "min": 60.0}, "Temperature": {"max": 25.0, "min": 18.0}, "SoilMoisture": {"max": 80.0, "min": 70.0}, "LightIntensity": {"max": 800.0, "min": 300.0}}
\.


--
-- Data for Name: scheduled_events; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.scheduled_events (event_id, frequency, execution_time, sensor_id, greenhouse_id, parameter, value) FROM stdin;
\.


--
-- Data for Name: sensors; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.sensors (sensor_id, area_id, type, name, unit, threshold_range, domain, greenhouse_id) FROM stdin;
13	23	NPK	NPK Sensor	mg/kg	{"K": {"max": 300, "min": 200}, "N": {"max": 100, "min": 50}, "P": {"max": 200, "min": 150}}	{"max": 1000, "min": 0}	28
12	23	Humidity	Humidity Sensor	%	{"max": 85, "min": 80}	{"max": 100, "min": 0}	28
10	22	Temperature	Temperature Sensor	°C	{"max": 30, "min": 25}	{"max": 100, "min": -50}	28
11	22	Humidity	Humidity Sensor	%	{"max": 85, "min": 75}	{"max": 100, "min": 0}	28
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.users (user_id, username, email, password_hash, telegram_user_id) FROM stdin;
3	thatsnegar	thatsnegar@gmail.com	\\x24326224313224614e776270656b3655396a36536f685a505252764c75514d4a776943424142442f52713331684746336a3077755567416473534d61	\N
4	negar	negar.polito@it.com	\\x243262243132246b557575527354766c4f77354c722f46364e2e65452e673776336b73712e6b33524e4c7644697650523676536d742f355468473247	\N
5	sam	sam@polito.it	\\x243262243132246e524a2f756f66584e546866627039327167706e2f4f7649326770376178457955534f5a364279714b4d392f5a645432383232484f	\N
6	jzk	sam@polito.it	\\x243262243132246a5842724b58374e4a3959496a68497567314c4d6d656e627a6e5748544f654167734377543572476b564933456169764164563275	\N
7	test	test@polito.it	\\x243262243132242e4473676f7376394b4373543874524d37714b623465392f70305a596a796233527242597637393055324f684a39684756776f2f4b	\N
8	test1	test@polito.it	\\x24326224313224426354694b35444178583065524f746d6c424f4f382e494533396c682f526b2e344a4a664267426c6451495241465a596c30545257	\N
9	test3	test@gmail.com	\\x24326224313224636c6e67304243594338733059515562684839636365427a694b6f636638626878514c667236414f793055346b2e34625334437732	\N
10	test4	test@gmail.com	\\x24326224313224566256514742456f4438585476585062424e4f7268756b4159646e45394f777478736777704238666179635365793738456b72486d	\N
11	test6	test@gmail.com	\\x243262243132247665735850706832526a3363425741542e754d5a594f4b7445484953625370302f50754d574d38682e4d6a762f724f4c4173666f2e	\N
13	thatsnegar123	thatsnegar@gmail.com	\\x24326224313224547134463779506e764535483832353343426d4a4d75516a4e35364c48565767706f4c6c4a666d5a3338387878633378657a6e7461	\N
14	thatsnegar1234	thatsnegar@gmail.com	\\x243262243132242f364954326552354a7237524976472f426a4442492e42683579786e777159373859596579512e63413772366a35436264505a6671	\N
15	someone	thatsnegar@gmail.com	\\x24326224313224633163714645614f72634b3876786b6c776e3855542e6e2f68347a5066424f522f645544582e6131486a676e59576f353037685957	\N
16	newuser3	test@gmail.com	\\x243262243132246433662f68716d4631506e63486d682e76304b71734f72426937744647393641616c546d42375a3036524465693138705136356b61	\N
17	user45	thatsnegar@gmail.com	\\x24326224313224686d566871344139536c7972436f502f33666e415a755a53307558494c2e564361595539795848445978666e78557774324d715547	\N
18	user456	thatsnegar@gmail.com	\\x2432622431322437477452386746397a77567a544f57792f4b7466554f3154413544624b444a68684837654a79536d654679526c4d32667759437065	\N
19	testuser5	thatsnegar@gmail.com	\\x2432622431322452466f6461664254314862746238367544643430692e554477784342783637744a53582e684e313973746d3174324f7a3047457661	\N
20	negggar	negar.abdi@studenti.polito.it	\\x2432622431322455716438526a696a50707851736d626a414965772e756269575149465052583276503750494a703246784c5835366b6555516c302e	\N
21	testingfinal	testingfinal@gmail.com	\\x243262243132246a522e364e41497a777a72326e34636552333656754f59314e45376f4a356a746b56694566726d4a646b7878614d7931724c776f2e	\N
22	newuser123	newuser123@gmail.com	\\x24326224313224576d6642786e2e6472346c793137524237396d337265656d452e77476f4c75464370655034474b5837694e734d6c7948346b62464b	\N
2	username	thatsnegar@gmail.com	\\x243262243132246378306272593044362f314e526358504a4a514d74754d374c504d2e3830374d34335743472e4e5131716142356434436e73794353	\N
0	Lorenzo	s346742@studenti.polito.it	\\x24326224313224732f64633664424a70456e37767069487a657a756f2e384f476952797863556433536c592f61336165505475464e4a41784643544f	2070801980
\.


--
-- Name: areas_area_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.areas_area_id_seq', 23, true);


--
-- Name: availabledevices_device_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.availabledevices_device_id_seq', 9, true);


--
-- Name: availablesensors_sensor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.availablesensors_sensor_id_seq', 1, false);


--
-- Name: devices_device_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.devices_device_id_seq', 83, true);


--
-- Name: greenhouses_greenhouse_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.greenhouses_greenhouse_id_seq', 28, true);


--
-- Name: plants_plant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.plants_plant_id_seq', 1, false);


--
-- Name: scheduled_events_event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.scheduled_events_event_id_seq', 9, true);


--
-- Name: sensors_sensor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.sensors_sensor_id_seq', 13, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.users_user_id_seq', 22, true);


--
-- Name: area_plants area_plants_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.area_plants
    ADD CONSTRAINT area_plants_pkey PRIMARY KEY (area_id, plant_id);


--
-- Name: areas areas_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT areas_pkey PRIMARY KEY (area_id);


--
-- Name: availabledevices availabledevices_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.availabledevices
    ADD CONSTRAINT availabledevices_pkey PRIMARY KEY (device_id);


--
-- Name: availablesensors availablesensors_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.availablesensors
    ADD CONSTRAINT availablesensors_pkey PRIMARY KEY (sensor_id);


--
-- Name: devices devices_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (device_id);


--
-- Name: greenhouses greenhouses_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.greenhouses
    ADD CONSTRAINT greenhouses_pkey PRIMARY KEY (greenhouse_id);


--
-- Name: otps otps_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.otps
    ADD CONSTRAINT otps_pkey PRIMARY KEY (telegram_user_id);


--
-- Name: plants plants_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.plants
    ADD CONSTRAINT plants_pkey PRIMARY KEY (plant_id);


--
-- Name: scheduled_events scheduled_events_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.scheduled_events
    ADD CONSTRAINT scheduled_events_pkey PRIMARY KEY (event_id);


--
-- Name: sensors sensors_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensors_pkey PRIMARY KEY (sensor_id);


--
-- Name: devices unique_greenhouse_device; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT unique_greenhouse_device UNIQUE (greenhouse_id, name);


--
-- Name: greenhouses unique_name_per_user; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.greenhouses
    ADD CONSTRAINT unique_name_per_user UNIQUE (user_id, name);


--
-- Name: users unique_telegram_user_id; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT unique_telegram_user_id UNIQUE (telegram_user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: devices devices_greeenhouse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_greeenhouse_id_fkey FOREIGN KEY (greenhouse_id) REFERENCES public.greenhouses(greenhouse_id) ON DELETE CASCADE;


--
-- Name: area_plants fk_area; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.area_plants
    ADD CONSTRAINT fk_area FOREIGN KEY (area_id) REFERENCES public.areas(area_id) ON DELETE CASCADE;


--
-- Name: area_plants fk_area_plants_greenhouse; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.area_plants
    ADD CONSTRAINT fk_area_plants_greenhouse FOREIGN KEY (greenhouse_id) REFERENCES public.greenhouses(greenhouse_id) ON DELETE CASCADE;


--
-- Name: areas fk_greenhouse; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT fk_greenhouse FOREIGN KEY (greenhouse_id) REFERENCES public.greenhouses(greenhouse_id) ON DELETE CASCADE;


--
-- Name: area_plants fk_plant; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.area_plants
    ADD CONSTRAINT fk_plant FOREIGN KEY (plant_id) REFERENCES public.plants(plant_id) ON DELETE CASCADE;


--
-- Name: greenhouses greenhouses_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.greenhouses
    ADD CONSTRAINT greenhouses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: scheduled_events scheduled_events_greenhouse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.scheduled_events
    ADD CONSTRAINT scheduled_events_greenhouse_id_fkey FOREIGN KEY (greenhouse_id) REFERENCES public.greenhouses(greenhouse_id);


--
-- Name: scheduled_events scheduled_events_sensor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.scheduled_events
    ADD CONSTRAINT scheduled_events_sensor_id_fkey FOREIGN KEY (sensor_id) REFERENCES public.sensors(sensor_id);


--
-- Name: sensors sensors_area_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensors_area_id_fkey FOREIGN KEY (area_id) REFERENCES public.areas(area_id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT CREATE ON SCHEMA public TO iotproject;


--
-- PostgreSQL database dump complete
--


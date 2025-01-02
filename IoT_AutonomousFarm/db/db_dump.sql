--
-- PostgreSQL database dump
--

-- Dumped from database version 16.6 (Ubuntu 16.6-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.6 (Ubuntu 16.6-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: devices; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.devices (
    device_id integer NOT NULL,
    greenhouse_id integer NOT NULL,
    name character varying(100) NOT NULL,
    type character varying(100) NOT NULL,
    CONSTRAINT device_name_check CHECK (((name)::text = ANY (ARRAY[('DeviceConnector'::character varying)::text, ('HumidityManagement'::character varying)::text, ('LightManagement'::character varying)::text, ('NutrientManagement'::character varying)::text, ('DataAnalysis'::character varying)::text, ('TimeShift'::character varying)::text, ('ThingSpeakAdaptor'::character varying)::text, ('TelegramBot'::character varying)::text, ('ThingSpeakAdaptor'::character varying)::text]))),
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
    thing_speak_channel_read_api_key character varying(20),
    thing_speak_channel_write_api_key character varying(20)
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
-- Name: plants; Type: TABLE; Schema: public; Owner: iotproject
--

CREATE TABLE public.plants (
    plant_id integer NOT NULL,
    greenhouse_id integer NOT NULL,
    name character varying(100) NOT NULL,
    species character varying(100) NOT NULL,
    thing_speak_channel_read_api_key character varying(20),
    thing_speak_channel_write_api_key character varying(20)
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
    greenhouse_id integer NOT NULL,
    event_type character varying(100) NOT NULL,
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone NOT NULL,
    frequency character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT event_values CHECK (((event_type)::text = ANY ((ARRAY['Irrigation'::character varying, 'Fertilization'::character varying, 'Lighting'::character varying])::text[]))),
    CONSTRAINT frequency_values CHECK (((frequency)::text = ANY ((ARRAY['Once'::character varying, 'Daily'::character varying, 'Weekly'::character varying, 'Monthly'::character varying])::text[]))),
    CONSTRAINT status_values CHECK (((status)::text = ANY ((ARRAY['Pending'::character varying, 'In action'::character varying, 'Compleated'::character varying])::text[])))
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
    greenhouse_id integer NOT NULL,
    plant_id integer,
    type character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    unit character varying(10),
    threshold_range jsonb,
    thing_speak_field character varying(20)
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
    password_hash character varying(255) NOT NULL
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
-- Data for Name: devices; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.devices (device_id, greenhouse_id, name, type) FROM stdin;
1	0	HumidityManagement	Microservices
2	0	LightManagement	Microservices
3	0	NutrientManagement	Microservices
0	0	DeviceConnector	DeviceConnector
4	0	DataAnalysis	Microservices
5	0	TimeShift	Microservices
6	0	ThingSpeakAdaptor	ThingSpeakAdaptor
\.


--
-- Data for Name: greenhouses; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.greenhouses (greenhouse_id, user_id, name, location, thing_speak_channel_read_api_key, thing_speak_channel_write_api_key) FROM stdin;
0	0	greenhouse_0	Torino	E8FA7YO31E86NVDU	DIOMNEBEJT9EW5PQ
\.


--
-- Data for Name: plants; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.plants (plant_id, greenhouse_id, name, species, thing_speak_channel_read_api_key, thing_speak_channel_write_api_key) FROM stdin;
0	0	basil	Lamiaceae	0HDA85CB4QXLVFQC	YO4BG26YPBCFX427
\.


--
-- Data for Name: scheduled_events; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.scheduled_events (event_id, greenhouse_id, event_type, start_time, end_time, frequency, status, created_at) FROM stdin;
\.


--
-- Data for Name: sensors; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.sensors (sensor_id, greenhouse_id, plant_id, type, name, unit, threshold_range, thing_speak_field) FROM stdin;
0	0	\N	Temperature	DTH22	Cel	{"max": 30.0, "min": 15.0}	\N
5	0	\N	Humidity	DTH22	%	{"max": 70.0, "min": 40.0}	\N
2	0	0	SoilMoisture	SoilMoisture	%	{"max": 60.0, "min": 20.0}	\N
4	0	\N	LightIntensity	LightIntensity	Lux	{"max": 10000.0, "min": 1000.0}	\N
3	0	0	pH	pH	\N	{"max": 7.5, "min": 5.5}	\N
1	0	0	NPK	NPK	mg/L	{"K": {"max": 800.0, "min": 200.0}, "N": {"max": 800.0, "min": 200.0}, "P": {"max": 800.0, "min": 200.0}}	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: iotproject
--

COPY public.users (user_id, username, email, password_hash) FROM stdin;
0	Lorenzo	s346742@studenti.polito.it	 
\.


--
-- Name: devices_device_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.devices_device_id_seq', 1, false);


--
-- Name: greenhouses_greenhouse_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.greenhouses_greenhouse_id_seq', 1, false);


--
-- Name: plants_plant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.plants_plant_id_seq', 1, false);


--
-- Name: scheduled_events_event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.scheduled_events_event_id_seq', 1, false);


--
-- Name: sensors_sensor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.sensors_sensor_id_seq', 1, false);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iotproject
--

SELECT pg_catalog.setval('public.users_user_id_seq', 1, false);


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
-- Name: devices devices_greenhouse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_greenhouse_id_fkey FOREIGN KEY (greenhouse_id) REFERENCES public.greenhouses(greenhouse_id);


--
-- Name: greenhouses greenhouses_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.greenhouses
    ADD CONSTRAINT greenhouses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: plants plants_greenhouse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.plants
    ADD CONSTRAINT plants_greenhouse_id_fkey FOREIGN KEY (greenhouse_id) REFERENCES public.greenhouses(greenhouse_id) ON DELETE CASCADE;


--
-- Name: scheduled_events scheduled_events_greenhouse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.scheduled_events
    ADD CONSTRAINT scheduled_events_greenhouse_id_fkey FOREIGN KEY (greenhouse_id) REFERENCES public.greenhouses(greenhouse_id) ON DELETE CASCADE;


--
-- Name: sensors sensors_greenhouse_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensors_greenhouse_id_fkey FOREIGN KEY (greenhouse_id) REFERENCES public.greenhouses(greenhouse_id) ON DELETE CASCADE;


--
-- Name: sensors sensors_plant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iotproject
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensors_plant_id_fkey FOREIGN KEY (plant_id) REFERENCES public.plants(plant_id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT CREATE ON SCHEMA public TO iotproject;


--
-- PostgreSQL database dump complete
--


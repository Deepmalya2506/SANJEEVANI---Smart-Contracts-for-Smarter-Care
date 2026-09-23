-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.abdm_mock_hfr (
  mvp_hfr_id text NOT NULL,
  official_hfr_id text,
  hospital_name text,
  source_record_id bigint,
  address text,
  latitude double precision,
  longitude double precision,
  source text,
  geom USER-DEFINED,
  CONSTRAINT abdm_mock_hfr_pkey PRIMARY KEY (mvp_hfr_id)
);
CREATE TABLE public.hospitals (
  hospital_id uuid NOT NULL DEFAULT gen_random_uuid(),
  mvp_hfr_id text NOT NULL UNIQUE,
  hospital_name character varying NOT NULL,
  verification_status character varying NOT NULL,
  profile_status character varying NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT hospitals_pkey PRIMARY KEY (hospital_id),
  CONSTRAINT fk_hospitals_mvp_hfr FOREIGN KEY (mvp_hfr_id) REFERENCES public.abdm_mock_hfr(mvp_hfr_id)
);
CREATE TABLE public.users (
  user_id uuid NOT NULL DEFAULT gen_random_uuid(),
  auth_user_id uuid NOT NULL UNIQUE,
  hospital_id uuid NOT NULL UNIQUE,
  admin_name character varying NOT NULL,
  user_mail character varying,
  id_proof_reference character varying,
  profile_completed boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (user_id),
  CONSTRAINT fk_users_auth FOREIGN KEY (auth_user_id) REFERENCES auth.users(id),
  CONSTRAINT fk_users_hospital FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id)
);
CREATE TABLE public.hospital_wallets (
  wallet_id uuid NOT NULL DEFAULT gen_random_uuid(),
  hospital_id uuid NOT NULL UNIQUE,
  address character varying NOT NULL UNIQUE,
  network character varying NOT NULL,
  verified boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT hospital_wallets_pkey PRIMARY KEY (wallet_id),
  CONSTRAINT fk_wallets_hospital FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id)
);
CREATE TABLE public.hospital_payment_accounts (
  payment_account_id uuid NOT NULL DEFAULT gen_random_uuid(),
  hospital_id uuid NOT NULL UNIQUE,
  provider character varying NOT NULL,
  upi_id character varying NOT NULL,
  verification_status character varying NOT NULL,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT hospital_payment_accounts_pkey PRIMARY KEY (payment_account_id),
  CONSTRAINT fk_payment_accounts_hospital FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id)
);
CREATE TABLE public.equipment_assets (
  asset_id uuid NOT NULL DEFAULT gen_random_uuid(),
  hospital_id uuid NOT NULL,
  equipment_type character varying NOT NULL,
  name character varying NOT NULL,
  serial_number character varying,
  condition_status character varying NOT NULL,
  availability_status character varying NOT NULL,
  shareable boolean DEFAULT true,
  location USER-DEFINED,
  hourly_rate numeric CHECK (hourly_rate >= 0::numeric),
  metadata jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT equipment_assets_pkey PRIMARY KEY (asset_id),
  CONSTRAINT fk_equipment_hospital FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id)
);
CREATE TABLE public.reservations (
  reservation_id uuid NOT NULL DEFAULT gen_random_uuid(),
  asset_id uuid NOT NULL,
  borrower_hospital_id uuid NOT NULL,
  starts_at timestamp with time zone NOT NULL,
  ends_at timestamp with time zone NOT NULL,
  hold_expires_at timestamp with time zone NOT NULL,
  status character varying NOT NULL,
  idempotency_key character varying NOT NULL UNIQUE,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT reservations_pkey PRIMARY KEY (reservation_id),
  CONSTRAINT fk_reservations_asset FOREIGN KEY (asset_id) REFERENCES public.equipment_assets(asset_id),
  CONSTRAINT fk_reservations_borrower FOREIGN KEY (borrower_hospital_id) REFERENCES public.hospitals(hospital_id)
);
CREATE TABLE public.loans (
  loan_id uuid NOT NULL DEFAULT gen_random_uuid(),
  reservation_id uuid NOT NULL UNIQUE,
  asset_id uuid NOT NULL,
  borrower_hospital_id uuid NOT NULL,
  lender_hospital_id uuid NOT NULL,
  borrower_wallet character varying,
  lender_wallet character varying,
  terms_hash character varying,
  loan_status character varying NOT NULL,
  amount numeric NOT NULL CHECK (amount >= 0::numeric),
  onchain_loan_id character varying UNIQUE,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT loans_pkey PRIMARY KEY (loan_id),
  CONSTRAINT fk_loans_borrower FOREIGN KEY (borrower_hospital_id) REFERENCES public.hospitals(hospital_id),
  CONSTRAINT fk_loans_lender FOREIGN KEY (lender_hospital_id) REFERENCES public.hospitals(hospital_id),
  CONSTRAINT fk_loans_reservation FOREIGN KEY (reservation_id) REFERENCES public.reservations(reservation_id),
  CONSTRAINT fk_loans_asset FOREIGN KEY (asset_id) REFERENCES public.equipment_assets(asset_id)
);
CREATE TABLE public.payments (
  payment_id uuid NOT NULL DEFAULT gen_random_uuid(),
  loan_id uuid NOT NULL,
  provider character varying NOT NULL,
  provider_order_id character varying NOT NULL UNIQUE,
  provider_payment_id character varying UNIQUE,
  charge_amount numeric NOT NULL CHECK (charge_amount >= 0::numeric),
  currency character varying NOT NULL,
  purpose character varying NOT NULL,
  status character varying NOT NULL,
  signature_verified boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT payments_pkey PRIMARY KEY (payment_id),
  CONSTRAINT fk_payments_loan FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
);
CREATE TABLE public.payment_webhook_events (
  webhook_event_id uuid NOT NULL DEFAULT gen_random_uuid(),
  provider_event_id character varying NOT NULL UNIQUE,
  provider_order_id character varying NOT NULL,
  event_type character varying NOT NULL,
  payload jsonb NOT NULL,
  processed boolean DEFAULT false,
  processed_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT payment_webhook_events_pkey PRIMARY KEY (webhook_event_id)
);
CREATE TABLE public.blockchain_txns (
  tx_id uuid NOT NULL DEFAULT gen_random_uuid(),
  loan_id uuid NOT NULL,
  tx_hash character varying NOT NULL UNIQUE,
  chain_id bigint NOT NULL,
  contract_address character varying NOT NULL,
  contract_version character varying,
  function_name character varying,
  event_name character varying,
  block_number bigint,
  status character varying NOT NULL,
  metadata jsonb,
  submitted_at timestamp with time zone,
  confirmed_at timestamp with time zone,
  CONSTRAINT blockchain_txns_pkey PRIMARY KEY (tx_id),
  CONSTRAINT fk_blockchain_txns_loan FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
);
CREATE TABLE public.loan_state_events (
  event_id uuid NOT NULL DEFAULT gen_random_uuid(),
  loan_id uuid NOT NULL,
  previous_state character varying,
  new_state character varying NOT NULL,
  actor_type character varying NOT NULL,
  actor_id uuid,
  source character varying NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT loan_state_events_pkey PRIMARY KEY (event_id),
  CONSTRAINT fk_loan_state_events_loan FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
);
CREATE TABLE public.activity_events (
  activity_id uuid NOT NULL DEFAULT gen_random_uuid(),
  hospital_id uuid NOT NULL,
  user_id uuid NOT NULL,
  entity_type character varying NOT NULL,
  entity_id uuid NOT NULL,
  event_type character varying NOT NULL,
  metadata jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT activity_events_pkey PRIMARY KEY (activity_id),
  CONSTRAINT fk_activity_hospital FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id),
  CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.notifications (
  notification_id uuid NOT NULL DEFAULT gen_random_uuid(),
  hospital_id uuid NOT NULL,
  loan_id uuid,
  channel character varying NOT NULL,
  type character varying NOT NULL,
  status character varying NOT NULL,
  provider_message_id character varying,
  attempt_count integer DEFAULT 0,
  error_message text,
  created_at timestamp with time zone DEFAULT now(),
  sent_at timestamp with time zone,
  CONSTRAINT notifications_pkey PRIMARY KEY (notification_id),
  CONSTRAINT fk_notifications_hospital FOREIGN KEY (hospital_id) REFERENCES public.hospitals(hospital_id),
  CONSTRAINT fk_notifications_loan FOREIGN KEY (loan_id) REFERENCES public.loans(loan_id)
);
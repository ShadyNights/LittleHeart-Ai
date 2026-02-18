CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('patient', 'doctor', 'admin')) DEFAULT 'patient',
    full_name TEXT NOT NULL,
    phone TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, full_name, role)
  VALUES (new.id, COALESCE(new.raw_user_meta_data->>'full_name', 'Unnamed Patient'), 'patient');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

CREATE TABLE IF NOT EXISTS public.patient_inputs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) NOT NULL,
    age INT NOT NULL CHECK (age BETWEEN 13 AND 55),
    trimester INT NOT NULL CHECK (trimester BETWEEN 1 AND 3),
    trimester_weeks INT NOT NULL CHECK (trimester_weeks BETWEEN 1 AND 45),
    blood_pressure INT NOT NULL CHECK (blood_pressure BETWEEN 0 AND 2),
    hemoglobin FLOAT NOT NULL CHECK (hemoglobin BETWEEN 0.0 AND 25.0),
    heart_rate INT NOT NULL CHECK (heart_rate BETWEEN 40 AND 200),
    swelling BOOLEAN NOT NULL DEFAULT FALSE,
    headache_severity INT NOT NULL CHECK (headache_severity BETWEEN 0 AND 3),
    vaginal_bleeding BOOLEAN NOT NULL DEFAULT FALSE,
    diabetes_history BOOLEAN NOT NULL DEFAULT FALSE,
    previous_complications BOOLEAN NOT NULL DEFAULT FALSE,
    fever BOOLEAN NOT NULL DEFAULT FALSE,
    blurred_vision BOOLEAN NOT NULL DEFAULT FALSE,
    reduced_fetal_movement BOOLEAN NOT NULL DEFAULT FALSE,
    severe_abdominal_pain BOOLEAN NOT NULL DEFAULT FALSE,
    ip_address TEXT,
    user_agent TEXT,
    request_metadata JSONB, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.engine_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    input_id UUID REFERENCES public.patient_inputs(id) ON DELETE CASCADE NOT NULL UNIQUE,
    rule_risk TEXT NOT NULL CHECK (rule_risk IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    rule_score FLOAT,
    rule_flags JSONB,
    ml_risk TEXT CHECK (ml_risk IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    ml_probabilities JSONB,
    ml_confidence FLOAT,
    gemini_explanation JSONB,
    final_risk TEXT NOT NULL CHECK (final_risk IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    fusion_reason TEXT,
    analysis_status TEXT DEFAULT 'completed',
    rule_engine_version TEXT DEFAULT 'v2.1-clinical',
    ml_model_version TEXT DEFAULT 'xgb-maternal-v1.4',
    gemini_model_version TEXT DEFAULT 'gemini-2.0-flash',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) NOT NULL,
    current_state TEXT NOT NULL DEFAULT 'START',
    collected_data JSONB DEFAULT '{}',
    is_completed BOOLEAN DEFAULT FALSE,
    timeout_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE CASCADE NOT NULL,
    sender TEXT NOT NULL CHECK (sender IN ('user', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    input_id UUID REFERENCES public.patient_inputs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.user_profiles(id),
    alert_type TEXT NOT NULL,
    status TEXT CHECK (status IN ('pending', 'sent', 'acknowledged', 'failed')) DEFAULT 'pending',
    notified_provider_id UUID REFERENCES public.user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION public.create_alert_if_high()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.final_risk IN ('HIGH', 'CRITICAL') THEN
    INSERT INTO public.alerts (input_id, user_id, alert_type)
    VALUES (
        NEW.input_id,
        (SELECT user_id FROM public.patient_inputs WHERE id = NEW.input_id),
        'High Risk Detected'
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE OR REPLACE TRIGGER on_high_risk_detected
AFTER INSERT ON public.engine_results
FOR EACH ROW
EXECUTE PROCEDURE public.create_alert_if_high();

CREATE OR REPLACE FUNCTION public.insert_risk_history()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.patient_risk_history (user_id, final_risk, input_id)
  VALUES (
    (SELECT user_id FROM public.patient_inputs WHERE id = NEW.input_id),
    NEW.final_risk,
    NEW.input_id
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE OR REPLACE TRIGGER on_result_insert_populate_history
AFTER INSERT ON public.engine_results
FOR EACH ROW
EXECUTE PROCEDURE public.insert_risk_history();

CREATE OR REPLACE FUNCTION public.save_clinical_assessment_v3(
    p_user_id UUID,
    p_age INT,
    p_trimester INT,
    p_trimester_weeks INT,
    p_blood_pressure INT,
    p_hb FLOAT,
    p_hr INT,
    p_swelling BOOLEAN,
    p_headache INT,
    p_bleeding BOOLEAN,
    p_diabetes BOOLEAN,
    p_complications BOOLEAN,
    p_fever BOOLEAN,
    p_blurred_vision BOOLEAN,
    p_rfm BOOLEAN,
    p_abdominal_pain BOOLEAN,
    p_ip TEXT,
    p_rule_risk TEXT,
    p_rule_score FLOAT,
    p_rule_flags JSONB,
    p_ml_risk TEXT,
    p_ml_probs JSONB,
    p_ml_conf FLOAT,
    p_final_risk TEXT,
    p_fusion_reason TEXT,
    p_explanation JSONB,
    p_status TEXT
) RETURNS UUID AS $$
DECLARE
    v_input_id UUID;
BEGIN
    INSERT INTO public.patient_inputs (
        user_id, age, trimester, trimester_weeks, blood_pressure, 
        hemoglobin, heart_rate, swelling, headache_severity, vaginal_bleeding, 
        diabetes_history, previous_complications, fever, blurred_vision, 
        reduced_fetal_movement, severe_abdominal_pain, ip_address
    ) VALUES (
        p_user_id, p_age, p_trimester, p_trimester_weeks, p_blood_pressure, 
        p_hb, p_hr, p_swelling, p_headache, p_bleeding, 
        p_diabetes, p_complications, p_fever, p_blurred_vision, 
        p_rfm, p_abdominal_pain, p_ip
    ) RETURNING id INTO v_input_id;

    INSERT INTO public.engine_results (
        input_id, rule_risk, rule_score, rule_flags, 
        ml_risk, ml_probabilities, ml_confidence, 
        gemini_explanation, final_risk, analysis_status, fusion_reason
    ) VALUES (
        v_input_id, p_rule_risk, p_rule_score, p_rule_flags, 
        p_ml_risk, p_ml_probs, p_ml_conf, 
        p_explanation, p_final_risk, p_status, p_fusion_reason
    );

    INSERT INTO public.audit_logs (user_id, action, metadata, ip_address)
    VALUES (p_user_id, 'CLINICAL_ASSESSMENT_ATOMIC', jsonb_build_object('input_id', v_input_id, 'risk', p_final_risk), p_ip);

    RETURN v_input_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id),
    action TEXT NOT NULL,
    metadata JSONB,
    ip_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.patient_risk_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) NOT NULL,
    final_risk TEXT NOT NULL CHECK (final_risk IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    input_id UUID REFERENCES public.patient_inputs(id) ON DELETE CASCADE,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.patient_assignments (
    patient_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (patient_id, doctor_id)
);

CREATE OR REPLACE FUNCTION public.check_doctor_role()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT role FROM public.user_profiles WHERE id = NEW.doctor_id) != 'doctor' THEN
    RAISE EXCEPTION 'Only users with "doctor" role can be assigned to patients.';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE OR REPLACE TRIGGER enforce_doctor_assignment
BEFORE INSERT OR UPDATE ON public.patient_assignments
FOR EACH ROW EXECUTE PROCEDURE public.check_doctor_role();

CREATE TABLE IF NOT EXISTS public.model_drift_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    model_version TEXT NOT NULL,
    accuracy FLOAT,
    ece FLOAT, 
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_inputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.engine_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_risk_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.patient_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_drift_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own profile" ON public.user_profiles;
CREATE POLICY "Users view own profile" ON public.user_profiles FOR SELECT USING (auth.uid() = id);

CREATE OR REPLACE FUNCTION public.check_is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN (SELECT (role = 'admin') FROM public.user_profiles WHERE id = auth.uid());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP POLICY IF EXISTS "Admins view all profiles" ON public.user_profiles;
CREATE POLICY "Admins view all profiles" ON public.user_profiles FOR SELECT USING (public.check_is_admin());

DROP POLICY IF EXISTS "Only admin can update roles" ON public.user_profiles;
CREATE POLICY "Only admin can update roles" ON public.user_profiles FOR UPDATE USING (public.check_is_admin()) WITH CHECK (public.check_is_admin());

DROP POLICY IF EXISTS "Only admin can deactivate accounts" ON public.user_profiles;
CREATE POLICY "Only admin can deactivate accounts" ON public.user_profiles FOR UPDATE USING (public.check_is_admin()) WITH CHECK (is_active IS NOT NULL);

DROP POLICY IF EXISTS "Users cannot update their own role" ON public.user_profiles;
CREATE POLICY "Users cannot update their own role" ON public.user_profiles FOR UPDATE USING (auth.uid() = id) WITH CHECK (role = (SELECT role FROM public.user_profiles WHERE id = auth.uid() LIMIT 1));

DROP POLICY IF EXISTS "Users insert own inputs" ON public.patient_inputs;
CREATE POLICY "Users insert own inputs" ON public.patient_inputs FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users view own inputs" ON public.patient_inputs;
CREATE POLICY "Users view own inputs" ON public.patient_inputs FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Doctors view assigned patients" ON public.patient_inputs;
CREATE POLICY "Doctors view assigned patients" ON public.patient_inputs FOR SELECT USING (EXISTS (SELECT 1 FROM public.patient_assignments pa WHERE pa.patient_id = patient_inputs.user_id AND pa.doctor_id = auth.uid()) OR (SELECT role FROM public.user_profiles WHERE id = auth.uid()) = 'admin');

DROP POLICY IF EXISTS "No updates to patient inputs" ON public.patient_inputs;
CREATE POLICY "No updates to patient inputs" ON public.patient_inputs FOR UPDATE USING (false);

DROP POLICY IF EXISTS "No delete patient inputs" ON public.patient_inputs;
CREATE POLICY "No delete patient inputs" ON public.patient_inputs FOR DELETE USING (false);

DROP POLICY IF EXISTS "Users view own results" ON public.engine_results;
CREATE POLICY "Users view own results" ON public.engine_results FOR SELECT USING (EXISTS (SELECT 1 FROM public.patient_inputs i WHERE i.id = engine_results.input_id AND i.user_id = auth.uid()));

DROP POLICY IF EXISTS "Doctors view assigned results" ON public.engine_results;
CREATE POLICY "Doctors view assigned results" ON public.engine_results FOR SELECT USING (EXISTS (SELECT 1 FROM public.patient_inputs i JOIN public.patient_assignments pa ON pa.patient_id = i.user_id WHERE i.id = engine_results.input_id AND pa.doctor_id = auth.uid()) OR (SELECT role FROM public.user_profiles WHERE id = auth.uid()) = 'admin');

DROP POLICY IF EXISTS "Service role insert results" ON public.engine_results;
CREATE POLICY "Service role insert results" ON public.engine_results FOR INSERT WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS "No update engine results" ON public.engine_results;
CREATE POLICY "No update engine results" ON public.engine_results FOR UPDATE USING (false);

DROP POLICY IF EXISTS "No delete engine results" ON public.engine_results;
CREATE POLICY "No delete engine results" ON public.engine_results FOR DELETE USING (false);

DROP POLICY IF EXISTS "Users view own alerts" ON public.alerts;
CREATE POLICY "Users view own alerts" ON public.alerts FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Doctors view assigned alerts" ON public.alerts;
CREATE POLICY "Doctors view assigned alerts" ON public.alerts FOR SELECT USING (EXISTS (SELECT 1 FROM public.patient_assignments pa WHERE pa.patient_id = alerts.user_id AND pa.doctor_id = auth.uid()) OR (SELECT role FROM public.user_profiles WHERE id = auth.uid()) = 'admin');

DROP POLICY IF EXISTS "Service role insert alerts" ON public.alerts;
CREATE POLICY "Service role insert alerts" ON public.alerts FOR INSERT WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role insert audit logs" ON public.audit_logs;
CREATE POLICY "Service role insert audit logs" ON public.audit_logs FOR INSERT WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Users view own history" ON public.patient_risk_history;
CREATE POLICY "Users view own history" ON public.patient_risk_history FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Doctors view assigned history" ON public.patient_risk_history;
CREATE POLICY "Doctors view assigned history" ON public.patient_risk_history FOR SELECT USING (EXISTS (SELECT 1 FROM public.patient_assignments pa WHERE pa.patient_id = patient_risk_history.user_id AND pa.doctor_id = auth.uid()) OR (SELECT role FROM public.user_profiles WHERE id = auth.uid()) = 'admin');

DROP POLICY IF EXISTS "Admins view drift" ON public.model_drift_logs;
CREATE POLICY "Admins view drift" ON public.model_drift_logs FOR SELECT USING ((SELECT role FROM public.user_profiles WHERE id = auth.uid()) = 'admin');

DROP POLICY IF EXISTS "Users manage own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users manage own chat sessions" ON public.chat_sessions FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users manage own chat messages" ON public.chat_messages;
CREATE POLICY "Users manage own chat messages" ON public.chat_messages FOR ALL USING (EXISTS (SELECT 1 FROM public.chat_sessions s WHERE s.id = chat_messages.session_id AND s.user_id = auth.uid()));

CREATE INDEX IF NOT EXISTS idx_inputs_user_created ON public.patient_inputs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_results_input ON public.engine_results(input_id);
CREATE INDEX IF NOT EXISTS idx_results_final_risk_created ON public.engine_results(final_risk, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_results_high_risk ON public.engine_results(created_at DESC) WHERE final_risk IN ('HIGH', 'CRITICAL');
CREATE INDEX IF NOT EXISTS idx_alerts_user ON public.alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON public.alerts(status);
CREATE INDEX IF NOT EXISTS idx_audit_user ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_history_user ON public.patient_risk_history(user_id);
CREATE INDEX IF NOT EXISTS idx_assignments_doctor ON public.patient_assignments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON public.chat_messages(session_id, created_at);
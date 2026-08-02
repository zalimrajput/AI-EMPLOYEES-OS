CREATE TABLE whatsapp_contacts (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    organization_id UUID
    REFERENCES organizations(id)
    ON DELETE CASCADE,


    name TEXT,


    phone TEXT,


    customer_id UUID
    REFERENCES customers(id),


    created_at TIMESTAMPTZ DEFAULT NOW()

);



CREATE TABLE whatsapp_messages (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    contact_id UUID
    REFERENCES whatsapp_contacts(id),


    message TEXT,


    direction TEXT,


    ai_generated BOOLEAN DEFAULT FALSE,


    media JSONB DEFAULT '{}',


    created_at TIMESTAMPTZ DEFAULT NOW()

);
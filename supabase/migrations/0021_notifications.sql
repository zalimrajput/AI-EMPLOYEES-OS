CREATE TABLE notifications (

    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),


    user_id UUID
    REFERENCES users(id),


    title TEXT,


    message TEXT,


    type TEXT,


    read BOOLEAN DEFAULT FALSE,


    created_at TIMESTAMPTZ DEFAULT NOW()

);
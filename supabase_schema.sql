-- Create user_profiles table for storing user fitness data
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    age INTEGER,
    weight DECIMAL(5,2),
    height INTEGER,
    gender VARCHAR(20),
    goal VARCHAR(50),
    activity VARCHAR(50),
    diet VARCHAR(50),
    days INTEGER,
    living_situation VARCHAR(50) DEFAULT 'home',
    cooking_ability VARCHAR(50) DEFAULT 'can_cook',
    gym_access VARCHAR(50) DEFAULT 'full_gym',
    equipment_available TEXT[], -- Array of equipment
    dietary_restrictions TEXT[], -- Array of restrictions
    budget_level VARCHAR(20) DEFAULT 'moderate',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a trigger to automatically update updated_at
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) for better security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows users to access their own data
-- Note: You'll need to adjust this based on your authentication setup
CREATE POLICY "Users can view their own profile" ON user_profiles
    FOR SELECT USING (true); -- For now, allow all reads (adjust based on your auth)

CREATE POLICY "Users can insert their own profile" ON user_profiles
    FOR INSERT WITH CHECK (true); -- For now, allow all inserts (adjust based on your auth)

CREATE POLICY "Users can update their own profile" ON user_profiles
    FOR UPDATE USING (true); -- For now, allow all updates (adjust based on your auth)

-- Create workout_plans table for storing user workout plans
CREATE TABLE IF NOT EXISTS workout_plans (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    goal VARCHAR(100),
    split TEXT[], -- Array of workout split days
    days INTEGER DEFAULT 7,
    exercises JSONB, -- JSON array of exercises with sets, reps, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_workout_plans_user_id ON workout_plans(user_id);

-- Create a trigger to automatically update updated_at for workout_plans
CREATE TRIGGER update_workout_plans_updated_at 
    BEFORE UPDATE ON workout_plans 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) for workout_plans
ALTER TABLE workout_plans ENABLE ROW LEVEL SECURITY;

-- Create policies for workout_plans
CREATE POLICY "Users can view their own workout plans" ON workout_plans
    FOR SELECT USING (true); -- For now, allow all reads (adjust based on your auth)

CREATE POLICY "Users can insert their own workout plans" ON workout_plans
    FOR INSERT WITH CHECK (true); -- For now, allow all inserts (adjust based on your auth)

CREATE POLICY "Users can update their own workout plans" ON workout_plans
    FOR UPDATE USING (true); -- For now, allow all updates (adjust based on your auth)

CREATE POLICY "Users can delete their own workout plans" ON workout_plans
    FOR DELETE USING (true); -- For now, allow all deletes (adjust based on your auth)

-- Create meal_plans table for storing user meal plans
CREATE TABLE IF NOT EXISTS meal_plans (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    goal VARCHAR(100),
    ingredients TEXT[], -- Array of ingredients
    meals JSONB, -- JSON object containing meal details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON meal_plans(user_id);

-- Create a trigger to automatically update updated_at for meal_plans
CREATE TRIGGER update_meal_plans_updated_at 
    BEFORE UPDATE ON meal_plans 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) for meal_plans
ALTER TABLE meal_plans ENABLE ROW LEVEL SECURITY;

-- Create policies for meal_plans
CREATE POLICY "Users can view their own meal plans" ON meal_plans
    FOR SELECT USING (true); -- For now, allow all reads (adjust based on your auth)

CREATE POLICY "Users can insert their own meal plans" ON meal_plans
    FOR INSERT WITH CHECK (true); -- For now, allow all inserts (adjust based on your auth)

CREATE POLICY "Users can update their own meal plans" ON meal_plans
    FOR UPDATE USING (true); -- For now, allow all updates (adjust based on your auth)

CREATE POLICY "Users can delete their own meal plans" ON meal_plans
    FOR DELETE USING (true); -- For now, allow all deletes (adjust based on your auth)
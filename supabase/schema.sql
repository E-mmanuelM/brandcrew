-- BrandCrew — Supabase Schema
-- Run this in your Supabase SQL Editor: Dashboard → SQL Editor → paste → Run
-- This creates all tables needed for the content pipeline.

-- ════════════════════════════════════════════
-- CORE TABLES (required for the pipeline to work)
-- ════════════════════════════════════════════

CREATE TABLE research_topics (
  id uuid primary key default gen_random_uuid(),
  topic text not null,
  source_url text,
  relevance_score int check (relevance_score between 1 and 10),
  engagement_signal text,
  content_angle text,
  created_at timestamp default now(),
  used boolean default false
);

CREATE TABLE content_ideas (
  id uuid primary key default gen_random_uuid(),
  research_topic_id uuid references research_topics(id),
  hook text,
  angle_description text,
  angle text,
  content_type text,
  suggested_format text,
  ip_connection text,
  relevance_score integer,
  status text default 'pending' check (status in ('pending', 'approved', 'rejected')),
  created_at timestamp default now()
);

CREATE TABLE content_drafts (
  id uuid primary key default gen_random_uuid(),
  content_idea_id uuid references content_ideas(id),
  draft_text text not null,
  quality_score int,
  quality_breakdown jsonb,
  status text default 'draft' check (status in ('draft', 'passed', 'failed', 'approved', 'published', 'rejected', 'finalized', 'archived')),
  rejection_reason text,
  edit_notes text,
  retry_count int default 0,
  image_prompt text,
  image_url text,
  template_name text,
  template_vars jsonb,
  posted boolean default false,
  approved_at timestamp,
  created_at timestamp default now(),
  updated_at timestamp default now()
);

CREATE TABLE agent_logs (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  action text not null,
  status text,
  input_data text,
  notes text,
  details jsonb,
  output_summary text,
  started_at timestamp,
  completed_at timestamp,
  created_at timestamp default now()
);

-- ════════════════════════════════════════════
-- EXTENDED TABLES (populated over time)
-- ════════════════════════════════════════════

CREATE TABLE ip_library (
  id uuid primary key default gen_random_uuid(),
  category text check (category in ('case_study', 'framework', 'opinion', 'vocabulary', 'problem_solved')),
  title text not null,
  content text not null,
  tags text[],
  created_at timestamp default now()
);

CREATE TABLE published_posts (
  id uuid primary key default gen_random_uuid(),
  draft_id uuid references content_drafts(id),
  platform text default 'linkedin',
  published_at timestamp,
  post_url text,
  impressions int,
  engagements int,
  comments int,
  reposts int,
  updated_at timestamp
);

CREATE TABLE repurposed_content (
  id uuid primary key default gen_random_uuid(),
  source_draft_id uuid references content_drafts(id),
  platform text check (platform in ('x', 'substack', 'tiktok')),
  content text,
  status text default 'draft',
  created_at timestamp default now()
);

CREATE TABLE analytics_insights (
  id uuid primary key default gen_random_uuid(),
  week_start date,
  summary text,
  top_performing_topics text[],
  recommendations jsonb,
  created_at timestamp default now()
);

CREATE ROLE gizclaw_mem0 LOGIN PASSWORD 'gizclaw_mem0';
CREATE DATABASE gizclaw_mem0 OWNER gizclaw_mem0;
REVOKE CONNECT ON DATABASE gizclaw_mem0 FROM PUBLIC;
\connect gizclaw_mem0
CREATE EXTENSION vector;

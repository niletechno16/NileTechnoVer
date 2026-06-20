# 🤖  AI-Powered Customer Support Intelligence Platform

An end-to-end platform that automatically transforms customer support conversations into actionable business insights.

The system integrates with Chatwoot, analyzes customer conversations using multiple AI providers, stores structured data in SQL Server, and provides a comprehensive analytics dashboard for monitoring support operations and performance.

---

# 📋 Project Overview

This platform automates the entire post-support workflow.

Whenever a conversation is closed in Chatwoot, the system automatically:

1. Receives the closure event through a Webhook
2. Retrieves the complete conversation history from Chatwoot
3. Analyzes the conversation using AI models
4. Generates summaries and issue classifications
5. Stores structured data in SQL Server
6. Updates the analytics dashboard in real time

The platform helps organizations monitor support quality, measure team performance, and gain valuable insights from customer interactions.

---

# 🏗️ System Architecture

The project consists of two main components:

## 1. AI Automation Service (FastAPI)

Responsible for:

* Receiving Chatwoot Webhooks
* Fetching conversation history
* AI-powered conversation analysis
* Issue classification
* Resolution status detection
* Data processing and storage

## 2. Analytics Dashboard (Django)

Responsible for:

* KPI Monitoring
* Agent Performance Tracking
* Customer Analytics
* Issue Analysis
* Reporting & Filtering
* Role-Based Access Control
* Operational Insights

---

# ✨ Key Features

## AI Automation

* Automated conversation processing
* AI-generated summaries
* Automatic issue classification
* Resolution detection
* Multi-provider AI fallback architecture
* Real-time data synchronization

## Analytics Dashboard

* Interactive dashboard
* Customer insights
* Agent performance tracking
* Resolved vs unresolved metrics
* Common issue analysis
* Advanced date filtering
* Historical reporting
* KPI monitoring
* Role-based permissions
* Guest access mode

---

# 🤖 AI Architecture

The platform uses a multi-provider fallback mechanism:

Groq → Gemini → Cerebras

### Features

* Automatic failover
* Multiple API keys support
* High availability
* Improved reliability
* Continuous processing even during provider outages

### AI Outputs

* Conversation Summary
* Issue Classification
* Resolution Status
* Support Outcome Analysis

---

# 🗄️ Database

Microsoft SQL Server is used as the primary data source.

Main modules include:

### Customer Management

Stores customer information without duplication.

### Support Reports

Stores:

* Customer Information
* Agent Information
* Conversation Metadata
* AI Summaries
* Issue Classifications
* Resolution Status
* Timestamps

### Dashboard Analytics

Aggregated data used for:

* Performance Metrics
* Operational Reports
* Customer Insights
* Trend Analysis

---

# 👥 User Roles

The dashboard supports multiple access levels:

* Developer
* Owner
* Admin
* Agent
* Visitor (Guest Access)

Each role has its own permissions and visibility scope.

---

# 🔗 API Endpoints

## FastAPI Service

### POST /webhook

Receives Chatwoot conversation status events.

### GET /health

Application health check endpoint.

---

# ⚙️ Technologies Used

## Backend

* Python
* FastAPI
* Django
* Django REST Framework

## Database

* Microsoft SQL Server
* pymssql

## AI Providers

* Groq
* Google Gemini
* Cerebras

## Integrations

* Chatwoot API
* Webhooks

## Deployment

* Docker
* Render
* Gunicorn
* WhiteNoise
* UptimeRobot

## Version Control

* Git
* GitHub

---

# 🔐 Environment Variables

Required variables:

## Chatwoot

* CHATWOOT_URL
* ACCOUNT_ID
* ACCESS_TOKEN

## Groq

* GROQ_KEY_1 → GROQ_KEY_5

## Gemini

* GEMINI_KEY_1 → GEMINI_KEY_5

## Cerebras

* CEREBRAS_KEY_1 → CEREBRAS_KEY_4

## Database

* DB_SERVER
* DB_NAME
* DB_USER
* DB_PASSWORD
* DB_PORT

## Django

* SECRET_KEY
* DEBUG
* ALLOWED_HOSTS

---

# 📊 Dashboard Capabilities

The analytics dashboard provides:

* Support performance monitoring
* Agent productivity analysis
* Customer activity tracking
* Resolution rate monitoring
* Historical reporting
* Date-based filtering
* Operational KPIs
* Support trend analysis

---

# 🚀 Deployment

The platform is deployed using Render and Docker.

Features include:

* Auto Deploy from GitHub
* Health Monitoring
* Automatic Restart
* Continuous Delivery Workflow

---

# 🎯 Project Goal

The goal of this project is to transform unstructured customer support conversations into structured business intelligence that helps organizations:

* Improve support quality
* Measure team performance
* Reduce manual reporting effort
* Identify recurring issues
* Make data-driven decisions

---

# 👨‍💻 Author

Designed, developed, and deployed end-to-end by Nile Techno.

From idea validation and system architecture to AI integration, dashboard development, database design, and production deployment.

QUANTIVA — PROJECT SPECIFICATION FOR CODEX
1. Your Role
Act as a senior data scientist, machine learning engineer, Python developer, data engineer, and technical mentor.
We are building an original, production-inspired data science portfolio project called Quantiva — Retail Intelligence & Predictive Analytics.
I am a BSc Information Technology graduate with experience in Python, SQL, C#, .NET, Microsoft Azure, and relational databases. I have completed an introductory data science certification and university-level statistics coursework.
I want this project to strengthen my candidacy for Junior Data Scientist, Data Analyst, and Junior Data Engineer positions.
Build the application with me, explaining important data science concepts, architectural decisions, statistical methods, and machine learning techniques as we progress.
Do not simply generate code without helping me understand the implementation.
2. Project Objective
Develop an end-to-end retail analytics platform that:
1.	Ingests real-world retail transaction data.
2.	Cleans and validates raw records.
3.	Stores processed data in a relational database.
4.	Performs exploratory data analysis.
5.	Calculates meaningful business metrics.
6.	Identifies purchasing patterns and sales trends.
7.	Trains machine learning models to forecast sales.
8.	Evaluates model performance using appropriate statistical metrics.
9.	Provides an interactive analytics dashboard.
10.	Produces reproducible findings suitable for a professional data science portfolio.
The system must demonstrate practical data science methodology rather than merely presenting attractive visualizations.
3. Dataset
Use the UCI Machine Learning Repository's Online Retail dataset.
Dataset URL:
https://archive.ics.uci.edu/dataset/352/online+retail
The dataset contains approximately 541,909 transaction records from a UK-based online retailer between December 2010 and December 2011.
Important fields include:
•	InvoiceNo
•	StockCode
•	Description
•	Quantity
•	InvoiceDate
•	UnitPrice
•	CustomerID
•	Country
Download the dataset from its official source and document the download procedure.
Do not fabricate sales records or model results.
If the dataset cannot be downloaded automatically, provide instructions for downloading it manually.
4. Data Engineering Pipeline
Create a reproducible data ingestion and cleaning pipeline.
Requirements:
•	Load the original dataset.
•	Inspect column types and missing values.
•	Identify duplicate records.
•	Detect invalid quantities and prices.
•	Identify cancelled transactions.
•	Handle missing customer identifiers appropriately.
•	Parse transaction timestamps.
•	Calculate line-item revenue.
•	Preserve the original raw data.
•	Produce a cleaned dataset suitable for analysis.
Important: Do not automatically delete every negative-quantity transaction without investigation. Distinguish cancellations and returns from completed sales, and document the treatment of each.
Store cleaned data in SQLite using SQLAlchemy.
Design appropriate relational tables, indexes, and constraints.
Include SQL queries demonstrating:
•	JOIN operations
•	GROUP BY aggregations
•	Common Table Expressions
•	Window functions
•	Date-based aggregations
Ensure that the pipeline is repeatable and does not duplicate imported records.
5. Exploratory Data Analysis
Create Jupyter notebooks to investigate the dataset.
Required analysis:
Revenue Analysis
•	Total revenue
•	Monthly revenue
•	Daily revenue
•	Revenue growth
•	Average order value
Product Analysis
•	Top products by revenue
•	Top products by quantity sold
•	Product concentration
•	Slow-moving products
Customer Analysis
•	Number of identifiable customers
•	Purchase frequency
•	Customer spending distribution
•	Repeat purchasing behaviour
Geographic Analysis
•	Revenue by country
•	Transaction distribution by country
•	Geographic concentration
Statistical Analysis
Apply appropriate descriptive statistics, including:
•	Mean
•	Median
•	Standard deviation
•	Quartiles
•	Percentiles
•	Distribution analysis
•	Correlation analysis where meaningful
Explain what each statistical measure tells us about the business.
Produce clear visualizations using Plotly and Matplotlib.
Every major visualization should include a written interpretation.
6. Machine Learning and Forecasting
Develop a forecasting component that predicts daily retail revenue.
Forecasting Target
Predict daily completed-sales revenue for the next 7 days initially.
Investigate extending the forecast horizon to 30 days after evaluating model reliability.
Data Preparation
Aggregate eligible transactions into a daily revenue time series.
Account for:
•	Missing calendar dates
•	Returns and cancellations
•	Calendar effects
•	Seasonal patterns
•	Lagged revenue
•	Rolling averages
Avoid data leakage.
Use only information that would have been available at prediction time.
Models
Implement and compare:
1.	Naive forecasting baseline
2.	Seasonal naive forecasting baseline
3.	Linear Regression
4.	Random Forest Regressor
Start with simple models before introducing complexity.
Evaluation
Use chronological train/test splits and time-series cross-validation where appropriate.
Evaluate models using:
•	Mean Absolute Error (MAE)
•	Root Mean Squared Error (RMSE)
•	WAPE where appropriate
Do not use random train/test splitting for time-series forecasting.
Compare each machine learning model against the baseline.
Do not claim that machine learning improves forecasting unless the results support that conclusion.
Document limitations caused by the dataset's relatively short historical period.
Model Artifacts
Save the selected model and its required preprocessing configuration.
Record:
•	Training period
•	Validation period
•	Test period
•	Features used
•	Hyperparameters
•	Evaluation metrics
•	Model version
Ensure that saved models can be loaded and used for inference.
7. Customer Segmentation
Implement Recency, Frequency, Monetary (RFM) analysis.
Calculate:
•	Recency: Time since the customer's last eligible purchase
•	Frequency: Number of distinct completed purchase invoices
•	Monetary: Total eligible customer spending
Use these metrics to identify customer segments.
Create visualizations showing customer distribution across segments.
Optionally explore K-Means clustering after the basic RFM implementation works.
If clustering is implemented, explain feature scaling, cluster selection, and evaluation.
Ensure the analysis excludes customers without valid identifiers and clearly documents the treatment of returns.
8. Interactive Dashboard
Build a Streamlit application.
Use a professional dark navy visual theme with clear typography and restrained blue accents.
The interface should be polished, responsive, and suitable for demonstration during a job interview.
Page 1: Overview
Display:
•	Total revenue
•	Number of completed orders
•	Average order value
•	Number of identifiable customers
•	Revenue trend chart
•	Top-performing products
Page 2: Sales Analytics
Display:
•	Daily and monthly revenue
•	Sales trends
•	Country comparisons
•	Product performance
•	Date filters
Page 3: Customer Intelligence
Display:
•	Customer purchase frequency
•	Spending distributions
•	RFM segmentation
•	Customer segment comparisons
Page 4: Predictive Analytics
Display:
•	Historical daily revenue
•	Forecasted revenue
•	Actual versus predicted results
•	Model comparison
•	MAE and RMSE
•	Forecast horizon
Clearly distinguish historical evaluation results from future forecasts.
Page 5: Data Quality
Display:
•	Original record count
•	Cleaned record count
•	Missing values
•	Duplicate records
•	Cancelled transactions
•	Data-cleaning decisions
All dashboard metrics must be calculated from the processed dataset.
Never hardcode fabricated KPIs.
9. Proposed Project Structure
quantiva/
•	README.md
•	pyproject.toml
•	.gitignore
•	.env.example
•	data/
o	raw/
o	processed/
•	notebooks/
o	01_data_exploration.ipynb
o	02_statistical_analysis.ipynb
o	03_forecasting_experiments.ipynb
•	src/
o	quantiva/
	_init_.py
	config.py
	ingestion.py
	cleaning.py
	database.py
	analytics.py
	features.py
	forecasting.py
	segmentation.py
•	app/
o	Home.py
o	pages/
	1_Sales_Analytics.py
	2_Customer_Intelligence.py
	3_Predictive_Analytics.py
	4_Data_Quality.py
•	models/
•	reports/
o	figures/
o	findings.md
o	model_evaluation.md
•	tests/
o	test_cleaning.py
o	test_analytics.py
o	test_features.py
o	test_forecasting.py
•	scripts/
o	download_data.py
o	prepare_data.py
o	train_model.py
Adapt the structure if there is a clear engineering benefit, but explain major deviations.
Do not commit raw datasets, generated databases, secrets, or large model artifacts to Git unless their size, licensing, and repository requirements have been checked.
10. Engineering Requirements
Follow professional software engineering practices.
Requirements:
•	Modular, readable Python code.
•	Type hints for important functions.
•	Docstrings for public interfaces.
•	Centralized configuration.
•	Structured logging.
•	Meaningful exception handling.
•	Reproducible dependency management.
•	Automated tests using pytest.
•	Deterministic random seeds where applicable.
•	No hardcoded local file paths.
•	No unnecessary paid services.
•	No credentials committed to GitHub.
Prioritize simplicity, maintainability, and correctness.
The entire application must run locally without requiring a cloud subscription.
11. Documentation
Create a professional README.md containing:
1.	Project overview.
2.	Business problem.
3.	Dataset source and limitations.
4.	Technology stack.
5.	System architecture.
6.	Installation instructions.
7.	Data preparation instructions.
8.	How to launch the dashboard.
9.	Machine learning methodology.
10.	Model evaluation results.
11.	Screenshots.
12.	Key analytical findings.
13.	Future improvements.
Also create a concise technical report describing the project's data science methodology.
Include actual findings and metrics only after running the analyses.
12. Portfolio and CV Requirements
The final project must demonstrate skills relevant to entry-level data science recruitment.
Produce:
•	A functional application.
•	Reproducible data analysis.
•	A documented forecasting experiment.
•	SQL analytical queries.
•	An interactive dashboard.
•	Automated tests.
•	A professional GitHub README.
•	A short portfolio case study.
Once the project is complete, draft 3–5 accurate, results-based CV bullet points.
Do not invent achievements, forecasting accuracy, or performance improvements.
13. Development Phases
Implement the project incrementally.
Phase 1 — Foundation
Set up the repository, environment, dependencies, dataset ingestion, and cleaning pipeline.
Phase 2 — Analytics
Implement SQL storage, exploratory data analysis, business KPIs, and statistical analysis.
Phase 3 — Machine Learning
Develop forecasting baselines, feature engineering, model training, validation, and evaluation.
Phase 4 — Dashboard
Build the Streamlit interface and integrate analytics and predictions.
Phase 5 — Portfolio Finalization
Complete documentation, tests, screenshots, technical reports, and GitHub presentation.
Do not attempt to build everything in one enormous code-generation step.
Finish and validate each phase before moving to the next.
14. Definition of Done
The project is complete when:
•	The original dataset can be downloaded or imported.
•	The cleaning pipeline runs successfully.
•	The SQL database can be rebuilt.
•	Dashboard metrics reconcile with validated SQL calculations.
•	Statistical analysis notebooks execute successfully.
•	Forecasting models train without data leakage.
•	Model performance is compared with meaningful baselines.
•	The Streamlit dashboard runs locally.
•	Automated tests pass.
•	The README contains working setup instructions.
•	Results are reproducible.
•	The project is suitable for public GitHub presentation.
15. How I Want You to Work
I want to understand the data science behind the project.
At each phase:
1.	Explain what we are building.
2.	Explain why it matters for data science.
3.	Identify the statistical or machine learning concepts involved.
4.	Implement the required code.
5.	Run tests and inspect the results.
6.	Explain what the results mean.
7.	Identify any limitations.
8.	Recommend the next step.
Ask questions only when a decision materially affects the implementation.
Make sensible technical decisions independently where appropriate.
Prioritize a working, technically defensible portfolio project over unnecessary complexity.
16. Your First Task
Begin by:
1.	Inspecting the current workspace.
2.	Determining whether a repository already exists.
3.	Proposing the initial architecture.
4.	Identifying required Python packages.
5.	Creating the project structure.
6.	Setting up a reproducible local development environment.
7.	Implementing the dataset download and initial inspection.
8.	Running the first data-quality checks.
Explain the initial findings before proceeding to the full cleaning pipeline.
Start with Phase 1. Do not implement the entire project at once.
Additional Execution Instructions
This is the master project specification for Quantiva. Treat it as the authoritative requirements document throughout development.
I have already created the local project folder and GitHub repository named quantiva.
Before making changes, inspect the existing repository and Git configuration. Preserve any existing files and work.
Save the complete specification in the repository as PROJECT_SPECIFICATION.md so it remains available for future development sessions.
Follow the five development phases described in the specification.
Important development rules:
1.	Implement one phase at a time.
2.	Begin with Phase 1 only.
3.	Run tests and verify functionality before completing each phase.
4.	Explain significant architectural and data science decisions.
5.	Keep the application completely free and locally executable.
6.	Maintain clean, professional, portfolio-quality code.
7.	Commit completed, verified milestones to Git when appropriate, but do not push to GitHub without my approval.
8.	Do not proceed to the next phase until I explicitly approve it.
At the end of Phase 1, provide a detailed progress report covering what was implemented, what was tested, any outstanding problems, and the recommended next steps.
Begin implementing Phase 1 now.


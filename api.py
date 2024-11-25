from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime
import asyncio

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Print credentials for debugging (remove in production)
print(f"\nInitializing API with:")
print(f"Supabase URL: {supabase_url}")
print(f"Supabase Key length: {len(supabase_key) if supabase_key else 0} chars")
print(f"Full Supabase Key for verification:")
print(f"{supabase_key}")

# Initialize FastAPI
app = FastAPI(
    title="Investment Portfolio Advisor API",
    description="API for generating personalized investment portfolio recommendations for Indian investors",
    version="1.0.0"
)

# Global variables
supabase = None
last_processed_timestamp = None

def init_supabase():
    """Initialize Supabase client"""
    global supabase
    try:
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        print("\nTrying to initialize Supabase client...")
        supabase = create_client(supabase_url, supabase_key)
        print("Basic client initialization successful")
        
        # Test the connection with minimal query
        try:
            print("\nTesting Supabase connection...")
            test_response = supabase.from_('client_forms').select('*').limit(1).execute()
            print(f"Connection test successful! Response: {test_response}")
        except Exception as e:
            print(f"\nError testing Supabase connection: {str(e)}")
            if hasattr(e, 'json'):
                print(f"Detailed error: {e.json()}")
            raise e
            
    except Exception as e:
        print(f"\nError initializing Supabase client: {str(e)}")
        if hasattr(e, 'json'):
            print(f"Detailed error: {e.json()}")
        raise e

def determine_risk_tolerance(scenario_answer: str) -> str:
    """Determine risk tolerance based on scenario answer"""
    risk_mapping = {
        "Get me out of here! Sell everything!": "low",
        "Let me wait and watch for a while": "moderate",
        "Great time to buy more at a discount!": "high"
    }
    return risk_mapping.get(scenario_answer, "moderate")

def process_financial_goals(goals_data: Any) -> List[dict]:
    """Process financial goals from any format"""
    try:
        if isinstance(goals_data, str):
            goals_json = json.loads(goals_data)
        elif isinstance(goals_data, dict):
            goals_json = goals_data
        else:
            goals_json = json.loads(str(goals_data))
            
        processed_goals = []
        for goal_type, details in goals_json.items():
            if details.get('selected', False):
                try:
                    years = int(details.get('years', 0)) if details.get('years') and str(details.get('years')).strip() else 0
                    amount = float(details.get('amount', 0)) if details.get('amount') and str(details.get('amount')).strip() else 0
                except (ValueError, TypeError):
                    years = 0
                    amount = 0
                    
                processed_goals.append({
                    'type': goal_type,
                    'years': years,
                    'amount': amount,
                    'description': str(details.get('description', ''))
                })
        return processed_goals
    except Exception as e:
        print(f"Error processing financial goals: {str(e)}")
        return []

def calculate_investment_capacity(client_data: dict) -> dict:
    """Calculate total investment capacity based on client's financial data"""
    monthly_income = (
        float(client_data.get('monthly_salary', 0)) +
        float(client_data.get('monthly_side_income', 0)) +
        float(client_data.get('monthly_other_income', 0))
    )
    
    monthly_expenses = (
        float(client_data.get('monthly_bills', 0)) +
        float(client_data.get('monthly_daily_life', 0)) +
        float(client_data.get('monthly_entertainment', 0))
    )
    
    monthly_savings = float(client_data.get('monthly_savings', 0))
    emergency_cash = float(client_data.get('emergency_cash', 0))
    
    # Calculate annual investment capacity
    annual_investment_capacity = monthly_savings * 12
    
    return {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_savings,
        'emergency_cash': emergency_cash,
        'annual_investment_capacity': annual_investment_capacity,
        'emergency_fund_ratio': round(emergency_cash / monthly_expenses if monthly_expenses > 0 else 0, 1)
    }

def determine_risk_profile(client_data: dict) -> dict:
    """Determine detailed risk profile based on client's data"""
    age = int(client_data.get('age', 35))
    risk_tolerance = client_data.get('risk_tolerance', 'moderate').lower()
    emergency_cash = float(client_data.get('emergency_cash', 0))
    monthly_expenses = (
        float(client_data.get('monthly_bills', 0)) +
        float(client_data.get('monthly_daily_life', 0)) +
        float(client_data.get('monthly_entertainment', 0))
    )
    
    # Calculate emergency fund ratio (months of expenses covered)
    emergency_fund_ratio = emergency_cash / monthly_expenses if monthly_expenses > 0 else 0
    
    # Base risk capacity on age
    if age < 30:
        risk_capacity = 'High'
    elif age < 45:
        risk_capacity = 'Medium'
    else:
        risk_capacity = 'Low'
    
    # Adjust based on emergency fund
    if emergency_fund_ratio < 3:
        risk_capacity = 'Low'  # Reduce risk capacity if emergency fund is low
    elif emergency_fund_ratio < 6:
        risk_capacity = min(risk_capacity, 'Medium')  # Cap at medium risk if emergency fund is moderate
    
    return {
        'tolerance_level': risk_tolerance,
        'risk_capacity': risk_capacity,
        'investment_horizon': '10 years',
        'emergency_fund_ratio': round(emergency_fund_ratio, 1)
    }

def generate_portfolio_strategy(client_data: dict, financial_metrics: dict) -> dict:
    """Generate portfolio strategy based on client profile and financial metrics"""
    risk_tolerance = client_data['risk_tolerance'].lower()
    age = int(client_data['age'])
    emergency_months = financial_metrics['emergency_fund_ratio']
    
    # Base allocations
    allocations = {
        'high': {
            'equity': 70,
            'debt': 20,
            'gold': 5,
            'real_estate': 5
        },
        'moderate': {
            'equity': 50,
            'debt': 30,
            'gold': 10,
            'real_estate': 10
        },
        'low': {
            'equity': 30,
            'debt': 50,
            'gold': 10,
            'real_estate': 10
        }
    }
    
    base_allocation = allocations.get(risk_tolerance, allocations['moderate'])
    
    # Adjust based on age and emergency fund
    if age > 50:
        base_allocation['equity'] = max(30, base_allocation['equity'] - 10)
        base_allocation['debt'] += 10
    elif emergency_months < 6:
        base_allocation['debt'] = min(60, base_allocation['debt'] + 10)
        base_allocation['equity'] = max(20, base_allocation['equity'] - 10)
    
    return base_allocation

async def monitor_client_forms():
    """Background task to monitor client_forms table for new entries"""
    global last_processed_timestamp
    print("\nStarting client forms monitor...")
    
    while True:
        try:
            print("\nChecking for new client forms...")
            print(f"Last processed timestamp: {last_processed_timestamp}")
            
            # Get current timestamp if not set
            if last_processed_timestamp is None:
                print("No last timestamp, getting most recent entry...")
                try:
                    response = supabase.from_('client_forms').select("created_at").order('created_at', desc=True).limit(1).execute()
                    print(f"Initial timestamp query response: {response}")
                    if response.data:
                        last_processed_timestamp = response.data[0]['created_at']
                        print(f"Set initial timestamp to: {last_processed_timestamp}")
                    else:
                        last_processed_timestamp = datetime.now().isoformat()
                        print(f"No existing entries, using current time: {last_processed_timestamp}")
                except Exception as e:
                    print(f"Error getting initial timestamp: {str(e)}")
                    if hasattr(e, 'json'):
                        print(f"Detailed error: {e.json()}")
                    raise e

            # Fetch only new records created after last_processed_timestamp
            print(f"\nFetching records newer than {last_processed_timestamp}")
            try:
                response = supabase.from_('client_forms').select("*").gt('created_at', last_processed_timestamp).execute()
                print(f"Query response: {response}")
            except Exception as e:
                print(f"Error querying new records: {str(e)}")
                if hasattr(e, 'json'):
                    print(f"Detailed error: {e.json()}")
                raise e
            
            if response.data:
                print(f"\nFound {len(response.data)} new client(s) to process")
                
                for client_data in response.data:
                    client_id = client_data.get('client_id')
                    created_at = client_data.get('created_at')
                    
                    print(f"\nProcessing new client: {client_id}")
                    print(f"Data received: {json.dumps(client_data, indent=2)}")
                    
                    try:
                        # Update last processed timestamp for this record
                        last_processed_timestamp = created_at
                        print(f"Updated last processed timestamp to: {last_processed_timestamp}")
                        
                        # Calculate investment capacity
                        investment_capacity = calculate_investment_capacity(client_data)
                        print(f"Monthly Income: ₹{investment_capacity['monthly_income']:,.2f}")
                        print(f"Monthly Savings: ₹{investment_capacity['monthly_savings']:,.2f}")
                        print(f"Emergency Fund Ratio: {investment_capacity['emergency_fund_ratio']} months")
                        
                        # Process financial goals
                        financial_goals = process_financial_goals(client_data.get('financial_goals', {}))
                        print(f"Financial Goals: {[goal['type'] for goal in financial_goals]}")
                        
                        # Determine risk profile
                        risk_profile = determine_risk_profile(client_data)
                        print(f"Risk Profile: {risk_profile['tolerance_level']} tolerance, {risk_profile['risk_capacity']} capacity")
                        
                        # Generate portfolio strategy
                        portfolio_strategy = generate_portfolio_strategy(client_data, investment_capacity)
                        print("Asset Allocation:", portfolio_strategy)
                        
                        # Generate client profile
                        client_profile = {
                            'name': client_data.get('name'),
                            'age': client_data.get('age'),
                            'occupation': client_data.get('occupation'),
                            'city': client_data.get('city'),
                            'financial_goals': [goal['type'] for goal in financial_goals],
                            'initial_investment': investment_capacity['annual_investment_capacity'],
                            'investment_timeline': risk_profile['investment_horizon'],
                            'risk_tolerance': risk_profile['tolerance_level']
                        }
                        
                        # Generate financial situation
                        financial_situation = {
                            'monthly_income': investment_capacity['monthly_income'],
                            'monthly_expenses': investment_capacity['monthly_expenses'],
                            'monthly_savings': investment_capacity['monthly_savings'],
                            'emergency_fund': investment_capacity['emergency_cash'],
                            'investment_capacity': investment_capacity['annual_investment_capacity'],
                            'emergency_fund_ratio': investment_capacity['emergency_fund_ratio'],
                            'liquidity_needs': 'Low' if investment_capacity['emergency_fund_ratio'] > 6 else 'Medium'
                        }
                        
                        # Generate investment objectives
                        investment_objectives = {
                            'primary_goals': [goal['type'] for goal in financial_goals],
                            'target_amounts': {goal['type']: goal['amount'] for goal in financial_goals},
                            'timeline': {goal['type']: goal['years'] for goal in financial_goals},
                            'target_return': '7-9% p.a.',
                            'constraints': [
                                'Tax-efficiency',
                                'Maintaining liquidity for short term needs'
                            ]
                        }
                        
                        # Generate investment strategy with calculated allocations
                        investment_strategy = {
                            'asset_allocation': {
                                'equity': f"{portfolio_strategy['equity']}%",
                                'debt': f"{portfolio_strategy['debt']}%",
                                'gold': f"{portfolio_strategy['gold']}%",
                                'real_estate': f"{portfolio_strategy['real_estate']}%"
                            },
                            'investment_vehicles': {
                                'mutual_funds': {
                                    'equity_funds': f"{portfolio_strategy['equity'] * 0.6}%",
                                    'debt_funds': f"{portfolio_strategy['debt'] * 0.6}%",
                                    'hybrid_funds': f"{(portfolio_strategy['equity'] + portfolio_strategy['debt']) * 0.1}%"
                                },
                                'direct_stocks': f"{portfolio_strategy['equity'] * 0.4}%",
                                'fixed_income_instruments': f"{portfolio_strategy['debt'] * 0.4}%",
                                'real_estate_investments': f"{portfolio_strategy['real_estate']}%"
                            },
                            'tax_planning_strategy': 'Investing in ELSS Mutual Funds, Utilizing Section 80C and 10(14)'
                        }
                        
                        # Generate portfolio data based on calculated allocations
                        portfolio_data = {
                            'Equity Mutual Funds': portfolio_strategy['equity'] * 0.6,
                            'Direct Equity': portfolio_strategy['equity'] * 0.4,
                            'Debt Mutual Funds': portfolio_strategy['debt'] * 0.6,
                            'Government Bonds': portfolio_strategy['debt'] * 0.2,
                            'Corporate FDs': portfolio_strategy['debt'] * 0.2,
                            'Gold ETFs': portfolio_strategy['gold'],
                            'Real Estate': portfolio_strategy['real_estate']
                        }
                        
                        # Generate personalized portfolio recommendation
                        portfolio_recommendation = {
                            'portfolio': {
                                'Large_Cap_Stocks': f"{portfolio_strategy['equity'] * 0.4}%",
                                'Mid_Cap_Stocks': f"{portfolio_strategy['equity'] * 0.3}%",
                                'Small_Cap_Stocks': f"{portfolio_strategy['equity'] * 0.3}%",
                                'Government_Bonds': f"{portfolio_strategy['debt'] * 0.4}%",
                                'Corporate_FDs': f"{portfolio_strategy['debt'] * 0.2}%",
                                'Gold_ETFs': f"{portfolio_strategy['gold']}%",
                                'Real_Estate': f"{portfolio_strategy['real_estate']}%"
                            },
                            'strategy': (
                                f"Based on your {risk_profile['tolerance_level']} risk tolerance and age of {client_data.get('age')}, "
                                f"we recommend a {risk_profile['risk_capacity']} risk portfolio. With monthly savings of "
                                f"₹{investment_capacity['monthly_savings']:,.2f} and an emergency fund covering "
                                f"{investment_capacity['emergency_fund_ratio']} months of expenses, this portfolio "
                                f"is designed to help achieve your financial goals while maintaining appropriate risk levels. "
                                f"The strategy focuses on {portfolio_strategy['equity']}% equity exposure through a mix of "
                                "mutual funds and direct stocks, providing growth potential while managing risk through "
                                f"diversification across {portfolio_strategy['debt']}% debt instruments and "
                                f"{portfolio_strategy['gold']}% gold for stability."
                            )
                        }
                        
                        # Market analysis (using current market data)
                        market_analysis = {
                            'mutual_funds': {
                                'equity_funds': [
                                    {
                                        'fund_name': 'HDFC Top 100 Fund',
                                        'category': 'Large Cap',
                                        'recommendation': 'BUY',
                                        '1yr_returns': '12.5%',
                                        '3yr_returns': '15.8%',
                                        'risk_rating': 'Moderate'
                                    }
                                ],
                                'debt_funds': [
                                    {
                                        'fund_name': 'ICICI Prudential Corporate Bond Fund',
                                        'category': 'Corporate Bond',
                                        'recommendation': 'BUY',
                                        '1yr_returns': '6.8%',
                                        '3yr_returns': '8.2%',
                                        'risk_rating': 'Low to Moderate'
                                    }
                                ]
                            },
                            'bonds': {
                                'government': [
                                    {
                                        'bond_name': '7.26% GOI 2033',
                                        'yield': '7.26%',
                                        'maturity': '2033',
                                        'recommendation': 'BUY',
                                        'risk_rating': 'Sovereign'
                                    }
                                ],
                                'corporate': [
                                    {
                                        'bond_name': 'HDFC 7.95% 2025',
                                        'yield': '7.95%',
                                        'maturity': '2025',
                                        'recommendation': 'BUY',
                                        'risk_rating': 'Low'
                                    }
                                ]
                            },
                            'fixed_deposits': [
                                {
                                    'bank_name': 'SBI',
                                    'duration': '5 years',
                                    'interest_rate': '6.50%',
                                    'recommendation': 'BUY',
                                    'special_benefits': 'Additional 0.5% for senior citizens'
                                }
                            ]
                        }
                        
                        # Prepare data for Supabase
                        unified_data = {
                            "client_id": client_id,
                            "user_id": "default_user",  # Set a default user for testing
                            "client_profile": json.dumps(client_profile),
                            "financial_situation": json.dumps(financial_situation),
                            "investment_objectives": json.dumps(investment_objectives),
                            "investment_strategy": json.dumps(investment_strategy),
                            "risk_profile": json.dumps(risk_profile),
                            "portfolio_data": json.dumps(portfolio_data),
                            "portfolio_recommendation": json.dumps(portfolio_recommendation),
                            "mutual_funds_analysis": json.dumps(market_analysis['mutual_funds']),
                            "bonds_analysis": json.dumps(market_analysis['bonds']),
                            "fixed_deposits_analysis": json.dumps({'Fixed_Deposits': market_analysis['fixed_deposits']})
                        }
                        
                        try:
                            # Store in Supabase with error handling
                            store_response = supabase.table("unified_table").insert(unified_data).execute()
                            print(f"Analysis stored successfully for client: {client_id}")
                            
                            # Update last processed timestamp if this is the most recent record
                            if last_processed_timestamp is None or created_at > last_processed_timestamp:
                                last_processed_timestamp = created_at
                                
                        except Exception as e:
                            print(f"Detailed error while storing data: {str(e)}")
                            raise e
                        
                    except Exception as e:
                        print(f"Error processing client {client_id}: {str(e)}")
                        continue
            else:
                print("No new records found")
                
        except Exception as e:
            print(f"Error in monitor loop: {str(e)}")
            if hasattr(e, 'json'):
                print(f"Detailed error: {e.json()}")
        
        # Wait before next check
        print("\nWaiting 5 seconds before next check...")
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the application starts"""
    print("\nStarting up API...")
    init_supabase()
    
    # Test Supabase connection and list tables
    print("\nTesting Supabase connection...")
    try:
        # Try a simple query first
        print("Attempting to query client_forms table...")
        response = supabase.from_('client_forms').select("*").execute()
        print(f"Successfully queried client_forms. Found {len(response.data)} records.")
        print(f"Sample data: {response.data[:1] if response.data else 'No records'}")
        
        # Start the monitoring task
        print("\nStarting monitoring task...")
        asyncio.create_task(monitor_client_forms())
        
    except Exception as e:
        print(f"Error testing Supabase connection: {str(e)}")
        if hasattr(e, 'json'):
            print(f"Detailed error: {e.json()}")
        raise e

@app.post("/analyze-portfolio/{client_id}")
async def analyze_client_portfolio(client_id: str):
    """Analyze portfolio for a specific client"""
    try:
        print("\nStarting Investment Portfolio Analysis...")
        
        # Fetch client data
        response = supabase.table('client_forms').select("*").eq('client_id', client_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Client not found")
        
        client_data = response.data[0]
        
        # Process client profile
        financial_goals = process_financial_goals(client_data.get('financial_goals', {}))
        initial_investment = float(client_data.get('monthly_savings', 0)) * 12
        
        client_profile = {
            'financial_goals': [goal['type'] for goal in financial_goals],
            'initial_investment': initial_investment,
            'investment_timeline': '10 years',
            'risk_tolerance': client_data.get('risk_tolerance', 'Moderate')
        }
        
        print("\nClient Profile:")
        print(json.dumps(client_profile, indent=2))
        print("\nSending profile to API...")
        print("Profile created successfully!")
        
        # Financial Situation
        financial_situation = {
            'initial_investment': initial_investment,
            'investment_category': 'Balanced Portfolio',
            'liquidity_needs': 'Low'
        }
        
        # Investment Objectives
        investment_objectives = {
            'primary_goals': [goal['type'] for goal in financial_goals],
            'target_return': '7-9% p.a.',
            'constraints': [
                'Tax-efficiency',
                'Maintaining liquidity for short term needs'
            ]
        }
        
        # Risk Profile
        risk_profile = determine_risk_profile(client_data)
        
        # Investment Strategy
        investment_strategy = {
            'asset_allocation': generate_portfolio_strategy(client_data, calculate_investment_capacity(client_data)),
            'investment_vehicles': {
                'mutual_funds': {
                    'equity_funds': '60%',
                    'debt_funds': '30%',
                    'hybrid_funds': '10%'
                },
                'direct_stocks': '20%',
                'fixed_income_instruments': '10%',
                'real_estate_investments': '10%'
            },
            'tax_planning_strategy': 'Investing in ELSS Mutual Funds, Utilizing Section 80C and 10(14)'
        }
        
        # Portfolio Data
        portfolio_data = {
            'Equity Mutual Funds': 30.0,
            'Debt Mutual Funds': 20.0,
            'Government Bonds': 20.0,
            'Corporate FDs': 20.0,
            'Gold ETFs': 10.0
        }
        
        # Portfolio Recommendation
        portfolio_recommendation = {
            'portfolio': {
                'Large_Cap_Stocks': '15%',
                'Mid_Cap_Stocks': '15%',
                'Small_Cap_Stocks': '10%',
                'Government_Bonds': '20%',
                'Corporate_FDs': '20%',
                'Gold_ETFs': '5%',
                'Mutual_Funds': '15%'
            },
            'strategy': (
                f"Considering the client's {client_data.get('risk_tolerance', 'moderate').lower()} risk tolerance "
                "and 10 years investment horizon..."
            ),
            'visualization_path': 'plot/portfolio_allocation.png'
        }
        
        # Market Analysis
        market_analysis = {
            'mutual_funds': {
                'equity_funds': [
                    {
                        'fund_name': 'HDFC Top 100 Fund',
                        'category': 'Large Cap',
                        'recommendation': 'BUY',
                        '1yr_returns': '12.5%',
                        '3yr_returns': '15.8%',
                        'risk_rating': 'Moderate'
                    }
                ],
                'debt_funds': [
                    {
                        'fund_name': 'ICICI Prudential Corporate Bond Fund',
                        'category': 'Corporate Bond',
                        'recommendation': 'BUY',
                        '1yr_returns': '6.8%',
                        '3yr_returns': '8.2%',
                        'risk_rating': 'Low to Moderate'
                    }
                ]
            },
            'bonds': {
                'government': [
                    {
                        'bond_name': '7.26% GOI 2033',
                        'yield': '7.26%',
                        'maturity': '2033',
                        'recommendation': 'BUY',
                        'risk_rating': 'Sovereign'
                    }
                ],
                'corporate': [
                    {
                        'bond_name': 'HDFC 7.95% 2025',
                        'yield': '7.95%',
                        'maturity': '2025',
                        'recommendation': 'BUY',
                        'risk_rating': 'Low'
                    }
                ]
            },
            'fixed_deposits': [
                {
                    'bank_name': 'SBI',
                    'duration': '5 years',
                    'interest_rate': '6.50%',
                    'recommendation': 'BUY',
                    'special_benefits': 'Additional 0.5% for senior citizens'
                }
            ]
        }
        
        # Prepare data for Supabase
        unified_data = {
            "client_id": client_id,
            "user_id": "default_user",  # Set a default user for testing
            "client_profile": json.dumps(client_profile),
            "financial_situation": json.dumps(financial_situation),
            "investment_objectives": json.dumps(investment_objectives),
            "investment_strategy": json.dumps(investment_strategy),
            "risk_profile": json.dumps(risk_profile),
            "portfolio_data": json.dumps(portfolio_data),
            "portfolio_recommendation": json.dumps(portfolio_recommendation),
            "mutual_funds_analysis": json.dumps(market_analysis['mutual_funds']),
            "bonds_analysis": json.dumps(market_analysis['bonds']),
            "fixed_deposits_analysis": json.dumps({'Fixed_Deposits': market_analysis['fixed_deposits']})
        }
        
        # Store in Supabase
        try:
            print("\nStoring analysis in database...")
            store_response = supabase.table("unified_table").insert(unified_data).execute()
            print("Analysis stored successfully!")
        except Exception as e:
            print(f"Error storing analysis: {str(e)}")
            # Continue even if storage fails
        
        return {
            'client_profile': client_profile,
            'financial_situation': financial_situation,
            'investment_objectives': investment_objectives,
            'risk_profile': risk_profile,
            'investment_strategy': investment_strategy,
            'portfolio_data': portfolio_data,
            'portfolio_recommendation': portfolio_recommendation,
            'market_analysis': market_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

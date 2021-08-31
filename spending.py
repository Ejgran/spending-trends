import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
from os import path
from datetime import timedelta
from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_html_components as html
import webbrowser
from threading import Timer

# Creates and organizes dataframe into relevant spending categories and
# returns a datafame of all the spending that occurred.
def organize_transactions():

    # load the csv into a pandas dataframe
    df = pd.read_csv('transactions.csv')

    # Remove unnecessary columns
    df = df.drop(columns = ['Labels','Notes', 'Transaction Type', 'Account Name'])

    # Remove transactions that transfer money between accounts
    df = df[df['Description'].str.contains('CHK 0127') == False]

    # Merge redundant categories and assign transactions to proper categories
    df.Category.replace(['Paycheck'], "Income", inplace = True)
    df.Category.replace(['Alcohol & Bars', 'Music'], "Entertainment", inplace = True)
    df.Category.replace(['Fast Food', 'Restaurants','Coffee Shops','Food & Dining','Newspapers & Magazines','Groceries'], "Food", inplace = True)
    df.Category.replace(['Air Travel'], "Travel", inplace = True)
    df.Category.replace(['Spa & Massage','Parking','Public Transportation','Rental Car & Taxi'], "Transport", inplace = True)
    df.Category.replace(['Gym','Pharmacy'], "Personal Care", inplace = True)
    df.Category.replace(['Clothing'], "Shopping", inplace = True)
    df.Category.replace(['Electronics & Software','Bank Fee','Pets','ATM Fee','Cash & ATM','Sporting Goods'], "Other", inplace = True)
    df['Category'] = np.where(df['Original Description'].str.contains('LINK SCOOTERS'), 'Transport', df['Category'] )
    df['Category'] = np.where(df['Original Description'].str.contains('AUSTIN BOULDERING'), 'Entertainment', df['Category'] )
    df['Category'] = np.where(df['Original Description'].str.contains('RIDE'), 'Transport', df['Category'] )
    df['Category'] = np.where(df['Original Description'].str.contains('MERIT'), 'Food', df['Category'] )
    df['Category'] = np.where(df['Original Description'].str.contains('WHETHAN'), 'Entertainment', df['Category'] )

    # Convert dates from strings to date objects and create new month/year col
    df['Date'] = pd.to_datetime(df['Date'])

    return df

# Gathers the transactions for the most recent full month and returns the
# dataframe of the transactions. Commented lines in case old data is needed
def trim_dates(df):
    # date_of_interest = datetime.date(2021,5,1) # april 2021
    # date_of_interest = datetime.date(2021,6,1) # may 2021
    # date_of_interest = datetime.date(2021,7,1) # june 2021
    date_of_interest = datetime.date.today() # July
    first_this_month = date_of_interest.replace(day = 1)
    first_this_month = pd.to_datetime(first_this_month)
    last_last_month = first_this_month - datetime.timedelta(days = 1)
    first_last_month = last_last_month.replace(day = 1)
    mask = (df['Date'] > first_last_month) & (df['Date'] <= last_last_month)
    df = df.loc[mask]

    return df

# Calcluates monthly categorical spending for a given month and appends it
# to a monthly categorical spending file, to be used for making a chart.
def spending_by_category(df):
    df['Amount'] = df.apply(lambda row: row['Amount'] if row['Category'] == 'Income' else row ['Amount'] *-1, axis = 1)
    df['Amount'] = df.apply(lambda row: row['Amount']*-1 , axis = 1)
    category_sums = df.groupby('Category')['Amount'].sum()
    list_cats = ['Entertainment','Food','Travel','Transport','Other','Personal Care','Shopping','Income']
    month = df['Date'].iloc[0]
    year_month = month.strftime('%b %Y')
    category_dict = {'Month': year_month}
    for i in range(len(list_cats)):
        if list_cats[i] in category_sums.index:
            category_dict[list_cats[i]] = category_sums.loc[list_cats[i]]
        else:
            category_dict[list_cats[i]] = 0

    # Checking if the file exists, appending dict if it does,
    # otherwise writes the dictionary to a new csv
    if path.exists('monthly_spending.csv'):
        category_spend_table = pd.read_csv('monthly_spending.csv')
        if year_month not in category_spend_table.Month.values:
            category_spend_table = category_spend_table.append(category_dict, ignore_index = True)
    else:
        category_spend_table = pd.DataFrame.from_dict([category_dict])

    category_spend_table.set_index('Month',inplace = True)
    category_spend_table.to_csv('monthly_spending.csv')

    return category_spend_table

# Displays multi-line graph of categorical monthly spending.
def category_graph():
    category_spend_table = pd.read_csv('monthly_spending.csv')
    figure = px.line(category_spend_table, x = 'Month', y = ['Entertainment','Food','Other','Personal Care','Shopping','Transport','Travel'],
        title = 'Monthly Spending by Category', labels = {"value": "Expenses ($)", "variable": "Category"})
    # figure.show()

    return figure

# Calculates monthly income, expenses, and net income and appends them to
# a file, to be used for making a chart.
def income_vs_expenses(df):
    month = df['Date'].iloc[0]
    year_month = month.strftime('%b %Y')
    category_sums = df.groupby('Category')['Amount'].sum()
    income = category_sums['Income']
    category_sums.drop(index = 'Income', inplace = True)
    total_expenses = category_sums.sum()
    net_income = income - total_expenses

    inc_exp_dict = {'Month': year_month, 'Total Income': income, 'Total Expenses': total_expenses, 'Net Income': net_income}

    if path.exists('income_vs_expenses.csv'):
        inc_exp_table = pd.read_csv('income_vs_expenses.csv')
        if year_month not in inc_exp_table.Month.values:
            inc_exp_table = inc_exp_table.append(inc_exp_dict, ignore_index = True)
    else:
        inc_exp_table = pd.DataFrame.from_dict([inc_exp_dict])

    inc_exp_table.set_index('Month',inplace = True)
    inc_exp_table.to_csv('income_vs_expenses.csv')

    return inc_exp_table

# Displays monthly income vs. expenses bar graph.
def inc_vs_exp_graph():
    inc_exp_table = pd.read_csv('income_vs_expenses.csv')
    figure = px.bar(inc_exp_table, x = 'Month', y = ['Total Expenses', 'Total Income'],
        title = 'Monthly Income vs. Expenses', barmode = 'group', labels = {"value": "Amount ($)", "variable": "Category"})
    # figure.show()

    return figure

# Displays monthly net income line graph. Uses same dataframe as income vs.
# expenses graph.
def net_income_graph():
    net_inc_table = pd.read_csv('income_vs_expenses.csv')
    figure = px.line(net_inc_table, x = 'Month', y = 'Net Income',
        title = 'Monthly Net Income', labels = {"Net Income": "Net Income ($)"})
    # figure.show()

    return figure

def dashboard(categorical_spend_graph, inc_vs_exp_graph, net_income_graph):

    app = JupyterDash(__name__)
    app.layout = html.Div([
        html.Div([
            html.H1("Personal Finance Summary", style = {'font-family' : 'Arial','text align': 'center'}),
            dcc.Graph(figure = net_income_graph)
        ]),
        html.Div([
            dcc.Graph(figure = categorical_spend_graph)
        ]),
        html.Div([
            dcc.Graph(figure = inc_vs_exp_graph)
        ])
    ])

    app.run_server(mode = 'external')
    webbrowser.open('http://localhost:8050/', new = 1)

def open_browser():
    webbrowser.open_new('http://localhost:8050/')

def main():

    df = organize_transactions() # dataframe of entire csv file
    df_last_month = trim_dates(df) # dataframe of only most recent months' spending
    category_spend = spending_by_category(df_last_month)
    categorical_spend_chart = category_graph()
    inc_vs_exp = income_vs_expenses(df_last_month)
    inc_vs_exp_chart = inc_vs_exp_graph()
    net_income_chart = net_income_graph()
    Timer(1, open_browser).start()
    dashboard(categorical_spend_chart, inc_vs_exp_chart, net_income_chart)

main()

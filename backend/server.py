from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import base64
import io
from PIL import Image
import json


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class ChartConfig(BaseModel):
    chart_type: str  # bar, line, scatter, pie, histogram, heatmap
    x_column: str
    y_column: Optional[str] = None
    color_scheme: Optional[str] = "viridis"
    title: Optional[str] = "Chart"
    width: Optional[int] = 800
    height: Optional[int] = 600

class ChartData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    data: str  # base64 encoded CSV data
    config: ChartConfig
    chart_image: Optional[str] = None  # base64 encoded chart image
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and return its structure and data preview"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    try:
        # Read the file content
        content = await file.read()
        content_str = content.decode('utf-8')

        # Parse CSV to get structure
        df = pd.read_csv(io.StringIO(content_str))

        # Get column info
        columns = df.columns.tolist()
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Get data preview (first 10 rows)
        preview_data = df.head(10).to_dict('records')

        # Encode data as base64
        data_base64 = base64.b64encode(content).decode('utf-8')

        return {
            "filename": file.filename,
            "data": data_base64,
            "columns": columns,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "preview": preview_data,
            "row_count": len(df),
            "column_count": len(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")

@api_router.post("/generate-chart")
async def generate_chart(chart_request: Dict[str, Any]):
    """Generate a chart from CSV data and configuration"""
    try:
        # Decode CSV data
        csv_data = base64.b64decode(chart_request['data']).decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data))

        config = chart_request['config']
        chart_type = config['chart_type']
        x_column = config['x_column']
        y_column = config.get('y_column')
        color_scheme = config.get('color_scheme', 'viridis')
        title = config.get('title', 'Chart')
        width = config.get('width', 800)
        height = config.get('height', 600)

        # Create figure
        plt.figure(figsize=(width/100, height/100))

        if chart_type == 'bar':
            if y_column and y_column in df.columns:
                plt.bar(df[x_column], df[y_column], color=plt.cm.get_cmap(color_scheme)(0.5))
                plt.ylabel(y_column)
            else:
                # Count plot for categorical data
                value_counts = df[x_column].value_counts()
                plt.bar(value_counts.index, value_counts.values, color=plt.cm.get_cmap(color_scheme)(0.5))
                plt.ylabel('Count')
            plt.xlabel(x_column)
            plt.xticks(rotation=45, ha='right')

        elif chart_type == 'line':
            if y_column and y_column in df.columns:
                plt.plot(df[x_column], df[y_column], color=plt.cm.get_cmap(color_scheme)(0.5), marker='o')
                plt.ylabel(y_column)
            else:
                # Line plot of index vs column
                plt.plot(df.index, df[x_column], color=plt.cm.get_cmap(color_scheme)(0.5), marker='o')
                plt.ylabel(x_column)
                plt.xlabel('Index')
            plt.xlabel(x_column if y_column else 'Index')

        elif chart_type == 'scatter':
            if y_column and y_column in df.columns:
                plt.scatter(df[x_column], df[y_column], c=plt.cm.get_cmap(color_scheme)(0.5), alpha=0.7)
                plt.ylabel(y_column)
                plt.xlabel(x_column)
            else:
                raise HTTPException(status_code=400, detail="Scatter plot requires both X and Y columns")

        elif chart_type == 'pie':
            if y_column and y_column in df.columns:
                # Group by x_column and sum y_column
                pie_data = df.groupby(x_column)[y_column].sum()
            else:
                # Count occurrences of x_column values
                pie_data = df[x_column].value_counts()

            colors = plt.cm.get_cmap(color_scheme)(range(len(pie_data)))
            plt.pie(pie_data.values, labels=pie_data.index, autopct='%1.1f%%', colors=colors)

        elif chart_type == 'histogram':
            plt.hist(df[x_column].dropna(), bins=30, color=plt.cm.get_cmap(color_scheme)(0.5), alpha=0.7)
            plt.xlabel(x_column)
            plt.ylabel('Frequency')

        elif chart_type == 'heatmap':
            # Create correlation heatmap for numeric columns
            numeric_df = df.select_dtypes(include=['number'])
            if len(numeric_df.columns) < 2:
                raise HTTPException(status_code=400, detail="Heatmap requires at least 2 numeric columns")

            correlation_matrix = numeric_df.corr()
            plt.imshow(correlation_matrix, cmap=color_scheme, aspect='auto')
            plt.colorbar()
            plt.xticks(range(len(correlation_matrix.columns)), correlation_matrix.columns, rotation=45, ha='right')
            plt.yticks(range(len(correlation_matrix.columns)), correlation_matrix.columns)

            # Add correlation values as text
            for i in range(len(correlation_matrix.columns)):
                for j in range(len(correlation_matrix.columns)):
                    plt.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                           ha='center', va='center', color='white' if abs(correlation_matrix.iloc[i, j]) > 0.5 else 'black')

        plt.title(title)
        plt.tight_layout()

        # Convert plot to base64 image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()

        # Save chart data to database
        chart_data = ChartData(
            filename=chart_request['filename'],
            data=chart_request['data'],
            config=ChartConfig(**config),
            chart_image=image_base64
        )

        await db.charts.insert_one(chart_data.dict())

        return {
            "id": chart_data.id,
            "chart_image": image_base64,
            "message": "Chart generated successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chart: {str(e)}")

@api_router.get("/charts")
async def get_charts():
    """Get all saved charts"""
    charts = await db.charts.find().to_list(1000)
    # Convert ObjectId to string and remove MongoDB _id field
    for chart in charts:
        if '_id' in chart:
            del chart['_id']
    return charts

@api_router.get("/chart/{chart_id}")
async def get_chart(chart_id: str):
    """Get a specific chart by ID"""
    chart = await db.charts.find_one({"id": chart_id})
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    # Remove MongoDB _id field
    if '_id' in chart:
        del chart['_id']
    return chart

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

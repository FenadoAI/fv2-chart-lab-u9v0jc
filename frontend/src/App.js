import { useState, useCallback } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, BarChart3, LineChart, PieChart, ScatterChart, BarChart, TrendingUp, Download, Palette } from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API = `${API_BASE}/api`;

const DataVisualizationPlayground = () => {
  const [csvData, setCsvData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [chartData, setChartData] = useState(null);
  const [chartConfig, setChartConfig] = useState({
    chart_type: 'bar',
    x_column: '',
    y_column: '',
    color_scheme: 'viridis',
    title: 'My Chart',
    width: 800,
    height: 600
  });

  const handleFileUpload = useCallback(async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/upload-csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setCsvData(response.data);
      setChartConfig(prev => ({
        ...prev,
        x_column: response.data.columns[0] || '',
        y_column: response.data.numeric_columns[0] || ''
      }));
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading file');
    } finally {
      setLoading(false);
    }
  }, []);

  const generateChart = useCallback(async () => {
    if (!csvData || !chartConfig.x_column) {
      setError('Please upload a CSV file and select columns');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/generate-chart`, {
        filename: csvData.filename,
        data: csvData.data,
        config: chartConfig
      });

      setChartData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error generating chart');
    } finally {
      setLoading(false);
    }
  }, [csvData, chartConfig]);

  const downloadChart = useCallback(() => {
    if (!chartData?.chart_image) return;

    const link = document.createElement('a');
    link.download = `${chartConfig.title.replace(/\s+/g, '_')}.png`;
    link.href = `data:image/png;base64,${chartData.chart_image}`;
    link.click();
  }, [chartData, chartConfig.title]);

  const chartTypeOptions = [
    { value: 'bar', label: 'Bar Chart', icon: BarChart3 },
    { value: 'line', label: 'Line Chart', icon: LineChart },
    { value: 'scatter', label: 'Scatter Plot', icon: ScatterChart },
    { value: 'pie', label: 'Pie Chart', icon: PieChart },
    { value: 'histogram', label: 'Histogram', icon: BarChart },
    { value: 'heatmap', label: 'Heatmap', icon: TrendingUp }
  ];

  const colorSchemes = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis',
    'Blues', 'Reds', 'Greens', 'Oranges', 'Purples',
    'coolwarm', 'RdYlBu', 'RdYlGn', 'Spectral'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Data Visualization Playground</h1>
          <p className="text-lg text-gray-600">Upload CSV files and create beautiful, interactive charts</p>
        </div>

        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertDescription className="text-red-700">{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload Section */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Upload Data
              </CardTitle>
              <CardDescription>Upload a CSV file to get started</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="csv-file">Select CSV File</Label>
                  <Input
                    id="csv-file"
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    disabled={loading}
                    className="mt-1"
                  />
                </div>

                {csvData && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold mb-2">File Info</h3>
                    <p className="text-sm text-gray-600">
                      <strong>File:</strong> {csvData.filename}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Rows:</strong> {csvData.row_count}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Columns:</strong> {csvData.column_count}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Chart Configuration */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Chart Configuration
              </CardTitle>
              <CardDescription>Customize your chart appearance</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="basic">Basic</TabsTrigger>
                  <TabsTrigger value="style">Style</TabsTrigger>
                </TabsList>

                <TabsContent value="basic" className="space-y-4">
                  <div>
                    <Label>Chart Type</Label>
                    <Select
                      value={chartConfig.chart_type}
                      onValueChange={(value) => setChartConfig(prev => ({ ...prev, chart_type: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {chartTypeOptions.map(option => {
                          const Icon = option.icon;
                          return (
                            <SelectItem key={option.value} value={option.value}>
                              <div className="flex items-center gap-2">
                                <Icon className="w-4 h-4" />
                                {option.label}
                              </div>
                            </SelectItem>
                          );
                        })}
                      </SelectContent>
                    </Select>
                  </div>

                  {csvData && (
                    <>
                      <div>
                        <Label>X-Axis Column</Label>
                        <Select
                          value={chartConfig.x_column}
                          onValueChange={(value) => setChartConfig(prev => ({ ...prev, x_column: value }))}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select column" />
                          </SelectTrigger>
                          <SelectContent>
                            {csvData.columns.map(column => (
                              <SelectItem key={column} value={column}>{column}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      {['bar', 'line', 'scatter'].includes(chartConfig.chart_type) && (
                        <div>
                          <Label>Y-Axis Column (Optional)</Label>
                          <Select
                            value={chartConfig.y_column}
                            onValueChange={(value) => setChartConfig(prev => ({ ...prev, y_column: value }))}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select column" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="">None</SelectItem>
                              {csvData.numeric_columns.map(column => (
                                <SelectItem key={column} value={column}>{column}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </>
                  )}
                </TabsContent>

                <TabsContent value="style" className="space-y-4">
                  <div>
                    <Label>Chart Title</Label>
                    <Input
                      value={chartConfig.title}
                      onChange={(e) => setChartConfig(prev => ({ ...prev, title: e.target.value }))}
                      placeholder="Enter chart title"
                    />
                  </div>

                  <div>
                    <Label className="flex items-center gap-2">
                      <Palette className="w-4 h-4" />
                      Color Scheme
                    </Label>
                    <Select
                      value={chartConfig.color_scheme}
                      onValueChange={(value) => setChartConfig(prev => ({ ...prev, color_scheme: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {colorSchemes.map(scheme => (
                          <SelectItem key={scheme} value={scheme}>{scheme}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Width (px)</Label>
                      <Input
                        type="number"
                        value={chartConfig.width}
                        onChange={(e) => setChartConfig(prev => ({ ...prev, width: parseInt(e.target.value) }))}
                        min="400"
                        max="1200"
                      />
                    </div>
                    <div>
                      <Label>Height (px)</Label>
                      <Input
                        type="number"
                        value={chartConfig.height}
                        onChange={(e) => setChartConfig(prev => ({ ...prev, height: parseInt(e.target.value) }))}
                        min="300"
                        max="800"
                      />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>

              <Button
                onClick={generateChart}
                disabled={loading || !csvData}
                className="w-full mt-4"
              >
                {loading ? 'Generating...' : 'Generate Chart'}
              </Button>
            </CardContent>
          </Card>

          {/* Chart Display */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Chart Preview
                </span>
                {chartData && (
                  <Button
                    onClick={downloadChart}
                    variant="outline"
                    size="sm"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-center min-h-[400px]">
              {chartData ? (
                <img
                  src={`data:image/png;base64,${chartData.chart_image}`}
                  alt="Generated Chart"
                  className="max-w-full max-h-full object-contain rounded-lg shadow-lg"
                />
              ) : (
                <div className="text-center text-gray-500">
                  <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>Upload a CSV file and configure your chart to see the preview</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Data Preview */}
        {csvData && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Data Preview</CardTitle>
              <CardDescription>First 10 rows of your data</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      {csvData.columns.map(column => (
                        <th key={column} className="text-left p-2 font-medium">{column}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {csvData.preview.map((row, index) => (
                      <tr key={index} className="border-b">
                        {csvData.columns.map(column => (
                          <td key={column} className="p-2">{row[column]}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DataVisualizationPlayground />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;

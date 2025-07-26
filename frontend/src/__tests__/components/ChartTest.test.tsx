import { render, screen } from '@testing-library/react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import * as d3 from 'd3';
import { init as echartsInit } from 'echarts';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

describe('Chart Libraries Integration', () => {
  it('renders Chart.js with react-chartjs-2', () => {
    const data = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [
        {
          label: 'Test Dataset',
          data: [65, 59, 80, 81, 56, 55],
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
        },
      ],
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: 'Test Chart',
        },
      },
    };

    render(<Line data={data} options={options} data-testid="test-chart" />);

    // Chart.js creates a canvas element
    const canvas = screen.getByTestId('test-chart');
    expect(canvas).toBeInTheDocument();
    expect(canvas.tagName).toBe('CANVAS');
  });

  it('loads D3.js library functions', () => {
    expect(typeof d3.scaleLinear).toBe('function');
    expect(typeof d3.select).toBe('function');
    expect(typeof d3.csv).toBe('function');

    // Test basic D3 scale functionality
    const scale = d3.scaleLinear().domain([0, 100]).range([0, 500]);

    expect(scale(50)).toBe(250);
  });

  it('loads ECharts library', () => {
    expect(typeof echartsInit).toBe('function');

    // Create a mock DOM element for ECharts
    const mockElement = document.createElement('div');
    mockElement.style.width = '400px';
    mockElement.style.height = '300px';

    // This should not throw an error
    expect(() => {
      const chart = echartsInit(mockElement);
      expect(chart).toBeDefined();
      chart.dispose(); // Clean up
    }).not.toThrow();
  });
});

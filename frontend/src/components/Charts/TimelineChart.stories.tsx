import React from "react";
import { TimelineChart } from "./TimelineChart";
import type { Meta, StoryObj } from "@storybook/react";
import { PortfolioSnapshot } from "../../types/timeline";

const mockData: PortfolioSnapshot[] = [
  {
    timestamp: 1690000000,
    collateral: 10000,
    borrowings: 2500,
    health_score: 1.3,
  },
  {
    timestamp: 1690600000,
    collateral: 11000,
    borrowings: 2600,
    health_score: 1.35,
  },
];

const meta: Meta<typeof TimelineChart> = {
  title: "Charts/TimelineChart",
  component: TimelineChart,
  parameters: {
    layout: "fullscreen",
  },
};
export default meta;

type Story = StoryObj<typeof TimelineChart>;

export const Primary: Story = {
  args: {
    snapshots: mockData,
  },
}; 
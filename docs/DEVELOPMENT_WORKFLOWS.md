# Development Workflows

> **Audience**: Claude Code & contributors  
> **Focus**: Practical development workflows for adding features, migrations, tests, and debugging

This document provides step-by-step workflows for common development tasks in the SmartWalletFX backend.

## 1. Adding New Domains/Features

### Domain Structure Analysis

The codebase follows a clear domain-driven structure:

```
app/
├── domain/
│   ├── schemas/          # Pydantic models for validation
│   └── interfaces/       # Repository interfaces
├── models/              # SQLAlchemy ORM models
├── repositories/        # Data access layer
├── usecase/            # Business logic layer
├── api/endpoints/      # HTTP endpoint controllers
└── services/           # External service integrations
```

### Workflow: Adding a New Domain

**Step 1**: Create domain schemas

```python
# app/domain/schemas/my_feature.py
from pydantic import BaseModel
from typing import Optional
import uuid

class MyFeatureCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MyFeatureResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
```

**Step 2**: Create SQLAlchemy model

```python
# app/models/my_feature.py
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class MyFeature(Base):
    __tablename__ = "my_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Step 3**: Create repository

```python
# app/repositories/my_feature_repository.py
from app.core.database import CoreDatabase
from app.models.my_feature import MyFeature
from app.utils.logging import Audit

class MyFeatureRepository:
    def __init__(self, database: CoreDatabase, audit: Audit):
        self.__database = database
        self.__audit = audit

    async def create(self, feature: MyFeature) -> MyFeature:
        async with self.__database.get_session() as session:
            session.add(feature)
            await session.commit()
            await session.refresh(feature)
            self.__audit.info("my_feature_created", feature_id=str(feature.id))
            return feature
```

**Step 4**: Create usecase

```python
# app/usecase/my_feature_usecase.py
from app.repositories.my_feature_repository import MyFeatureRepository
from app.domain.schemas.my_feature import MyFeatureCreate, MyFeatureResponse

class MyFeatureUsecase:
    def __init__(self, repo: MyFeatureRepository, config: Configuration, audit: Audit):
        self.__repo = repo
        self.__config = config
        self.__audit = audit

    async def create_feature(self, data: MyFeatureCreate) -> MyFeatureResponse:
        feature = MyFeature(name=data.name, description=data.description)
        created = await self.__repo.create(feature)
        return MyFeatureResponse.model_validate(created)
```

**Step 5**: Create endpoint

```python
# app/api/endpoints/my_feature.py
from fastapi import APIRouter
from app.usecase.my_feature_usecase import MyFeatureUsecase

class MyFeature:
    ep = APIRouter(tags=["my-feature"])

    def __init__(self, usecase: MyFeatureUsecase):
        self.__usecase = usecase
        self.ep.add_api_route("/my-features", self.create_feature, methods=["POST"])

    async def create_feature(self, data: MyFeatureCreate):
        return await self.__usecase.create_feature(data)
```

**Step 6**: Register in DI Container

```python
# app/di.py - Add to appropriate sections
def _initialize_repositories(self):
    # ... existing repositories
    my_feature_repo = MyFeatureRepository(database, audit)
    self.register_repository("my_feature", my_feature_repo)

def _initialize_usecases(self):
    # ... existing usecases
    my_feature_uc = MyFeatureUsecase(
        self.get_repository("my_feature"),
        self.get_core("config"),
        self.get_core("audit")
    )
    self.register_usecase("my_feature", my_feature_uc)

def _initialize_endpoints(self):
    # ... existing endpoints
    my_feature_endpoint = MyFeature(self.get_usecase("my_feature"))
    self.register_endpoint("my_feature", my_feature_endpoint)
```

## 2. Migration Creation Workflow

### Analyzing Existing Migrations

```bash
# List all migrations
ls migrations/versions/

# Example migration naming pattern:
0001_init.py                 # Initial schema
0002_add_portfolio_snapshot_cache_table.py
0003_rename_password_hash_to_hashed_password.py
0011_add_password_reset_table.py
0012_add_oauth_accounts_table.py
```

### Workflow: Creating a Migration

**Step 1**: Generate migration

```bash
cd backend
alembic revision --autogenerate -m "add my_feature table"
```

**Step 2**: Review generated migration

```python
# migrations/versions/XXXX_add_my_feature_table.py
def upgrade() -> None:
    op.create_table(
        'my_features',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_my_features_name', 'my_features', ['name'])

def downgrade() -> None:
    op.drop_index('ix_my_features_name', 'my_features')
    op.drop_table('my_features')
```

**Step 3**: Apply migration

```bash
alembic upgrade head
```

**Step 4**: Verify schema

```bash
# Connect to database and verify table creation
psql -d smartwallet_dev -c "\dt my_features"
```

## 3. Test Writing Patterns

### Test Structure Analysis

```
tests/
├── domains/              # Domain-specific tests
│   ├── auth/
│   │   ├── unit/        # Unit tests with mocks
│   │   └── integration/ # Integration tests with database
│   └── wallets/
├── infrastructure/       # Infrastructure tests
└── shared/fixtures/     # Shared test fixtures
```

### Unit Test Pattern

```python
# tests/domains/my_feature/unit/test_my_feature_usecase.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.usecase.my_feature_usecase import MyFeatureUsecase

@pytest.fixture
def mock_my_feature_repository():
    mock_repo = Mock()
    mock_repo.create = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    return mock_repo

@pytest.fixture
def my_feature_usecase(mock_my_feature_repository, mock_config, mock_audit):
    return MyFeatureUsecase(
        repo=mock_my_feature_repository,
        config=mock_config,
        audit=mock_audit
    )

@pytest.mark.asyncio
async def test_create_feature_success(my_feature_usecase, mock_my_feature_repository):
    # Arrange
    create_data = MyFeatureCreate(name="Test Feature")
    mock_feature = Mock(id=uuid.uuid4(), name="Test Feature")
    mock_my_feature_repository.create.return_value = mock_feature

    # Act
    result = await my_feature_usecase.create_feature(create_data)

    # Assert
    assert result.name == "Test Feature"
    mock_my_feature_repository.create.assert_called_once()
```

### Integration Test Pattern

```python
# tests/domains/my_feature/integration/test_my_feature_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_feature_endpoint(integration_async_client: AsyncClient):
    # Arrange
    feature_data = {"name": "Integration Test Feature"}

    # Act
    response = await integration_async_client.post(
        "/my-features",
        json=feature_data
    )

    # Assert
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Integration Test Feature"
    assert "id" in result
```

### Running Tests

```bash
# Run all tests quietly (Claude's preferred mode)
make test-quiet

# Run specific test file
pytest -q --tb=short --color=no tests/domains/my_feature/unit/test_my_feature_usecase.py

# Run tests with pattern matching
pytest -q --tb=short --color=no -k "test_create_feature"

# Run integration tests only
pytest -q --tb=short --color=no tests/domains/my_feature/integration/
```

## 4. Debugging Strategies

### Using DI Container for Debugging

```python
# Access any component through DI container
from app.di import DIContainer

di = DIContainer()
config = di.get_core("config")
user_repo = di.get_repository("user")
auth_usecase = di.get_usecase("auth")

# Test individual components
user = await user_repo.get_by_id(user_id)
```

### Database Debugging

```bash
# Connect to development database
psql -h postgres-dev -U devuser -d smartwallet_dev

# Check recent migrations
SELECT version_num FROM alembic_version;

# Inspect table structure
\d+ users
\d+ wallets
```

### Logging and Audit Trail

```python
# Enable debug logging in development
LOG_LEVEL=DEBUG

# Audit logs provide structured debugging info
self.__audit.info("operation_start", user_id=str(user.id), operation="create_wallet")
self.__audit.error("operation_failed", error=str(e), context={"user_id": str(user.id)})
```

### Testing Database Queries

```python
# Use test database session for query debugging
from tests.shared.fixtures.database import db_session

async with db_session() as session:
    result = await session.execute(
        select(User).where(User.email == "test@example.com")
    )
    user = result.scalar_one_or_none()
```

## 5. Frontend Development Workflows

### Frontend Architecture Overview

The frontend follows a modern React architecture with clear separation of concerns:

```
frontend/src/
├── components/          # Reusable UI components
│   ├── home/           # Domain-specific components
│   ├── auth/           # Authentication components
│   └── design-system/  # Design system components
├── pages/              # Page-level components (route handlers)
├── hooks/              # Custom React hooks
├── services/           # API service layer
├── store/              # Redux Toolkit slices
├── theme/              # Design system theme
├── types/              # TypeScript type definitions
└── utils/              # Utility functions
```

### Workflow: Adding a New Feature

**Step 1**: Define TypeScript interfaces

```typescript
// types/myFeature.ts
export interface MyFeatureData {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
}

export interface MyFeatureCreateRequest {
  name: string;
  description?: string;
}

export interface MyFeatureState {
  items: MyFeatureData[];
  loading: boolean;
  error: string | null;
}
```

**Step 2**: Create service layer

```typescript
// services/myFeature.ts
import apiClient from "./api";
import { MyFeatureData, MyFeatureCreateRequest } from "../types/myFeature";

export const myFeatureService = {
  async getAll(): Promise<MyFeatureData[]> {
    const response = await apiClient.get("/my-features");
    return response.data;
  },

  async create(data: MyFeatureCreateRequest): Promise<MyFeatureData> {
    const response = await apiClient.post("/my-features", data);
    return response.data;
  },

  async getById(id: string): Promise<MyFeatureData> {
    const response = await apiClient.get(`/my-features/${id}`);
    return response.data;
  },

  async update(
    id: string,
    data: Partial<MyFeatureCreateRequest>,
  ): Promise<MyFeatureData> {
    const response = await apiClient.put(`/my-features/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/my-features/${id}`);
  },
};
```

**Step 3**: Create Redux slice

```typescript
// store/myFeatureSlice.ts
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { myFeatureService } from "../services/myFeature";
import { MyFeatureState, MyFeatureData } from "../types/myFeature";

const initialState: MyFeatureState = {
  items: [],
  loading: false,
  error: null,
};

export const fetchMyFeatures = createAsyncThunk(
  "myFeature/fetchAll",
  async (_, { rejectWithValue }) => {
    try {
      return await myFeatureService.getAll();
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.message || "Failed to fetch features",
      );
    }
  },
);

export const createMyFeature = createAsyncThunk(
  "myFeature/create",
  async (data: MyFeatureCreateRequest, { rejectWithValue }) => {
    try {
      return await myFeatureService.create(data);
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.message || "Failed to create feature",
      );
    }
  },
);

const myFeatureSlice = createSlice({
  name: "myFeature",
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMyFeatures.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMyFeatures.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchMyFeatures.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(createMyFeature.fulfilled, (state, action) => {
        state.items.push(action.payload);
      });
  },
});

export const { clearError } = myFeatureSlice.actions;
export default myFeatureSlice.reducer;
```

**Step 4**: Create custom hook

```typescript
// hooks/useMyFeature.ts
import { useSelector, useDispatch } from "react-redux";
import { useCallback } from "react";
import { RootState } from "../store";
import {
  fetchMyFeatures,
  createMyFeature,
  clearError,
} from "../store/myFeatureSlice";
import { MyFeatureCreateRequest } from "../types/myFeature";

export const useMyFeature = () => {
  const dispatch = useDispatch();
  const { items, loading, error } = useSelector(
    (state: RootState) => state.myFeature,
  );

  const loadFeatures = useCallback(() => {
    dispatch(fetchMyFeatures());
  }, [dispatch]);

  const createFeature = useCallback(
    (data: MyFeatureCreateRequest) => {
      return dispatch(createMyFeature(data));
    },
    [dispatch],
  );

  const clearErrorMessage = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  return {
    features: items,
    loading,
    error,
    loadFeatures,
    createFeature,
    clearError: clearErrorMessage,
  };
};
```

**Step 5**: Create UI components

```typescript
// components/MyFeatureCard.tsx
import React from 'react';
import { Card, CardContent, Typography, CardActions, Button } from '@mui/material';
import { MyFeatureData } from '../types/myFeature';

interface MyFeatureCardProps {
  feature: MyFeatureData;
  onEdit?: (feature: MyFeatureData) => void;
  onDelete?: (id: string) => void;
}

export const MyFeatureCard: React.FC<MyFeatureCardProps> = ({
  feature,
  onEdit,
  onDelete,
}) => {
  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="h6" component="h3" gutterBottom>
          {feature.name}
        </Typography>
        {feature.description && (
          <Typography variant="body2" color="text.secondary">
            {feature.description}
          </Typography>
        )}
        <Typography variant="caption" display="block" sx={{ mt: 1 }}>
          Created: {new Date(feature.createdAt).toLocaleDateString()}
        </Typography>
      </CardContent>
      <CardActions>
        {onEdit && (
          <Button size="small" onClick={() => onEdit(feature)}>
            Edit
          </Button>
        )}
        {onDelete && (
          <Button size="small" color="error" onClick={() => onDelete(feature.id)}>
            Delete
          </Button>
        )}
      </CardActions>
    </Card>
  );
};
```

**Step 6**: Create page component

```typescript
// pages/MyFeaturePage.tsx
import React, { useEffect } from 'react';
import { Container, Typography, Box, Alert } from '@mui/material';
import { useMyFeature } from '../hooks/useMyFeature';
import { MyFeatureCard } from '../components/MyFeatureCard';

const MyFeaturePage: React.FC = () => {
  const { features, loading, error, loadFeatures } = useMyFeature();

  useEffect(() => {
    loadFeatures();
  }, [loadFeatures]);

  if (loading) {
    return (
      <Container>
        <Typography>Loading...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" gutterBottom>
        My Features
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box>
        {features.map(feature => (
          <MyFeatureCard
            key={feature.id}
            feature={feature}
            onEdit={feature => console.log('Edit:', feature)}
            onDelete={id => console.log('Delete:', id)}
          />
        ))}
      </Box>
    </Container>
  );
};

export default MyFeaturePage;
```

**Step 7**: Register slice in store

```typescript
// store/index.ts
import { configureStore } from "@reduxjs/toolkit";
import authSlice from "./authSlice";
import myFeatureSlice from "./myFeatureSlice"; // Add this import

export const store = configureStore({
  reducer: {
    auth: authSlice,
    myFeature: myFeatureSlice, // Add this line
    // ... other slices
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### Component Development Patterns

#### Material-UI Component Pattern

```typescript
// components/design-system/StyledButton.tsx
import React from 'react';
import { Button, ButtonProps, styled } from '@mui/material';

interface StyledButtonProps extends ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
}

const CustomButton = styled(Button, {
  shouldForwardProp: prop => prop !== 'variant',
})<StyledButtonProps>(({ theme, variant }) => ({
  ...(variant === 'primary' && {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    '&:hover': {
      backgroundColor: theme.palette.primary.dark,
    },
  }),
  ...(variant === 'danger' && {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText,
    '&:hover': {
      backgroundColor: theme.palette.error.dark,
    },
  }),
}));

export const StyledButton: React.FC<StyledButtonProps> = props => {
  return <CustomButton {...props} />;
};
```

#### Form Component Pattern

```typescript
// components/MyFeatureForm.tsx
import React, { useState } from 'react';
import { Box, TextField, Button, Alert } from '@mui/material';
import { useMyFeature } from '../hooks/useMyFeature';

interface MyFeatureFormProps {
  onSuccess?: () => void;
}

export const MyFeatureForm: React.FC<MyFeatureFormProps> = ({ onSuccess }) => {
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [validationError, setValidationError] = useState('');
  const { createFeature, loading, error } = useMyFeature();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      setValidationError('Name is required');
      return;
    }

    try {
      await createFeature(formData);
      setFormData({ name: '', description: '' });
      setValidationError('');
      onSuccess?.();
    } catch (err) {
      console.error('Failed to create feature:', err);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
      {(error || validationError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || validationError}
        </Alert>
      )}

      <TextField
        label="Name"
        value={formData.name}
        onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
        fullWidth
        margin="normal"
        required
      />

      <TextField
        label="Description"
        value={formData.description}
        onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
        fullWidth
        margin="normal"
        multiline
        rows={3}
      />

      <Button
        type="submit"
        variant="contained"
        disabled={loading}
        sx={{ mt: 2 }}
      >
        {loading ? 'Creating...' : 'Create Feature'}
      </Button>
    </Box>
  );
};
```

### Testing Frontend Components

#### Component Unit Test

```typescript
// __tests__/components/MyFeatureCard.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MyFeatureCard } from '../../components/MyFeatureCard';
import { MyFeatureData } from '../../types/myFeature';

const mockFeature: MyFeatureData = {
  id: '1',
  name: 'Test Feature',
  description: 'Test description',
  createdAt: '2025-01-01T00:00:00Z',
};

describe('MyFeatureCard', () => {
  it('renders feature information correctly', () => {
    render(<MyFeatureCard feature={mockFeature} />);

    expect(screen.getByText('Test Feature')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
    expect(screen.getByText(/Created:/)).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = jest.fn();
    render(<MyFeatureCard feature={mockFeature} onEdit={onEdit} />);

    fireEvent.click(screen.getByText('Edit'));
    expect(onEdit).toHaveBeenCalledWith(mockFeature);
  });

  it('calls onDelete when delete button is clicked', () => {
    const onDelete = jest.fn();
    render(<MyFeatureCard feature={mockFeature} onDelete={onDelete} />);

    fireEvent.click(screen.getByText('Delete'));
    expect(onDelete).toHaveBeenCalledWith('1');
  });
});
```

#### Redux Slice Test

```typescript
// __tests__/store/myFeatureSlice.test.ts
import { configureStore } from "@reduxjs/toolkit";
import myFeatureSlice, {
  fetchMyFeatures,
  clearError,
} from "../../store/myFeatureSlice";

const createTestStore = () => {
  return configureStore({
    reducer: {
      myFeature: myFeatureSlice,
    },
  });
};

describe("myFeatureSlice", () => {
  it("should handle fetchMyFeatures.pending", () => {
    const store = createTestStore();
    const action = { type: fetchMyFeatures.pending.type };

    store.dispatch(action);
    const state = store.getState().myFeature;

    expect(state.loading).toBe(true);
    expect(state.error).toBe(null);
  });

  it("should handle clearError", () => {
    const store = createTestStore();

    // First set an error
    store.dispatch({
      type: fetchMyFeatures.rejected.type,
      payload: "Test error",
    });
    expect(store.getState().myFeature.error).toBe("Test error");

    // Then clear it
    store.dispatch(clearError());
    expect(store.getState().myFeature.error).toBe(null);
  });
});
```

#### Custom Hook Test

```typescript
// __tests__/hooks/useMyFeature.test.tsx
import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { useMyFeature } from '../../hooks/useMyFeature';
import myFeatureSlice from '../../store/myFeatureSlice';

const createWrapper = () => {
  const store = configureStore({
    reducer: { myFeature: myFeatureSlice },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>{children}</Provider>
  );
};

describe('useMyFeature', () => {
  it('should provide initial state', () => {
    const { result } = renderHook(() => useMyFeature(), {
      wrapper: createWrapper(),
    });

    expect(result.current.features).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should provide action functions', () => {
    const { result } = renderHook(() => useMyFeature(), {
      wrapper: createWrapper(),
    });

    expect(typeof result.current.loadFeatures).toBe('function');
    expect(typeof result.current.createFeature).toBe('function');
    expect(typeof result.current.clearError).toBe('function');
  });
});
```

### Design System Integration

#### Creating Theme-Aware Components

```typescript
// components/design-system/ThemedCard.tsx
import React from 'react';
import { Card, CardProps, styled } from '@mui/material';

const StyledCard = styled(Card)(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[2],
  transition: theme.transitions.create(['box-shadow', 'transform'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    boxShadow: theme.shadows[4],
    transform: 'translateY(-2px)',
  },
}));

export const ThemedCard: React.FC<CardProps> = props => {
  return <StyledCard {...props} />;
};
```

#### Using Design Tokens

```typescript
// components/TokenExample.tsx
import React from 'react';
import { Box, Typography } from '@mui/material';
import * as tokens from '../theme/generated';

export const TokenExample: React.FC = () => {
  return (
    <Box
      sx={{
        padding: tokens.SizeSpacingMd,
        borderRadius: tokens.SizeRadiiMd,
        backgroundColor: tokens.ColorBackgroundSurface,
        border: `1px solid ${tokens.ColorBorderDefault}`,
      }}
    >
      <Typography
        sx={{
          fontSize: tokens.FontSizeH3,
          fontWeight: tokens.FontWeightSemibold,
          lineHeight: tokens.FontLineheightHeading,
          color: tokens.ColorTextPrimary,
        }}
      >
        Design Token Example
      </Typography>
    </Box>
  );
};
```

### Performance Optimization Patterns

#### Memoization Pattern

```typescript
// components/OptimizedFeatureList.tsx
import React, { memo, useMemo } from 'react';
import { Box } from '@mui/material';
import { MyFeatureCard } from './MyFeatureCard';
import { MyFeatureData } from '../types/myFeature';

interface OptimizedFeatureListProps {
  features: MyFeatureData[];
  searchTerm: string;
  onEdit: (feature: MyFeatureData) => void;
  onDelete: (id: string) => void;
}

export const OptimizedFeatureList = memo<OptimizedFeatureListProps>(({
  features,
  searchTerm,
  onEdit,
  onDelete,
}) => {
  const filteredFeatures = useMemo(() => {
    if (!searchTerm) return features;

    return features.filter(feature =>
      feature.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      feature.description?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [features, searchTerm]);

  return (
    <Box>
      {filteredFeatures.map(feature => (
        <MyFeatureCard
          key={feature.id}
          feature={feature}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </Box>
  );
});

OptimizedFeatureList.displayName = 'OptimizedFeatureList';
```

#### Lazy Loading Pattern

```typescript
// components/LazyFeatureComponent.tsx
import React, { Suspense, lazy } from 'react';
import { CircularProgress, Box } from '@mui/material';

const HeavyFeatureComponent = lazy(() => import('./HeavyFeatureComponent'));

export const LazyFeatureComponent: React.FC = () => {
  return (
    <Suspense
      fallback={
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      }
    >
      <HeavyFeatureComponent />
    </Suspense>
  );
};
```

### Frontend Development Commands

```bash
# Start development server
cd frontend
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Build for production
npm run build

# Preview production build
npm run preview

# Generate design tokens
npm run tokens:build

# Run type checking
npm run type-check
```

## Key Development Principles

### Backend Principles

1. **Follow the Layer Pattern**: Domain → Model → Repository → Usecase → Endpoint
2. **Use DI Container**: Register all new components in the dependency injection container
3. **Test Early**: Write unit tests for business logic, integration tests for flows
4. **Audit Everything**: Add audit logging for all significant operations
5. **Validate Input**: Use Pydantic schemas for all API inputs and outputs
6. **Handle Errors**: Use the centralized error handling for consistent responses

### Frontend Principles

1. **Component Composition**: Build complex UIs from simple, reusable components
2. **State Management**: Use Redux for global state, local state for component-specific data
3. **Type Safety**: Leverage TypeScript for compile-time error detection
4. **Performance First**: Use memoization, lazy loading, and code splitting
5. **Design System**: Follow Material-UI patterns and design tokens
6. **Test Coverage**: Unit test components, hooks, and slices thoroughly
7. **API Integration**: Use service layer for clean separation between UI and data

## Common Debugging Commands

### Backend

```bash
# Check application logs
docker-compose logs backend

# Database connection test
make db-test

# Run linting and formatting
make lint
make format

# Generate test coverage report
make test-cov

# Check for security issues
make bandit
make safety
```

### Frontend

```bash
# Check React DevTools in browser
# Install: https://react-devtools.netlify.app/

# Check Redux DevTools in browser
# Install: https://github.com/reduxjs/redux-devtools

# Debug build issues
npm run build -- --debug

# Analyze bundle size
npm run build && npx vite-bundle-analyzer dist

# Check TypeScript issues
npm run type-check

# Debug test failures
npm test -- --verbose

# Check for unused dependencies
npx depcheck
```

---

_Last updated: 19 July 2025_

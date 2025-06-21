# JWT Key Rotation Flow Diagrams

This file contains Mermaid diagrams for the JWT key rotation system that can be embedded in documentation.

## Key Lifecycle State Diagram

```mermaid
stateDiagram-v2
    [*] --> Active: Key promoted
    Active --> Grace: New key promoted
    Grace --> Retired: Grace period expires
    Retired --> [*]: Key removed
    
    note right of Active: Signing new tokens
    note right of Grace: Validating old tokens
    note right of Retired: No longer trusted
```

## Automated Rotation Workflow

```mermaid
graph TD
    subgraph "Automated Rotation System"
        A[Celery Beat Scheduler] -->|Every 5 minutes| B[Redis Lock Check]
        B -->|Lock Acquired| C[Rotation Task]
        B -->|Lock Contended| D[Exit Gracefully]
        C --> E[Check Key Grace Periods]
        E -->|Keys to Retire| F[Retire Old Keys]
        E -->|Active Key Expired| G[Promote Next Key]
        F --> H[Emit Audit Events]
        G --> H
        H --> I[Update Metrics]
        I --> J[Release Lock]
    end
    
    subgraph "Monitoring & Alerting"
        K[Prometheus Metrics] --> L[Grafana Dashboards]
        M[Slack Alerts] --> N[Incident Response]
        O[Structured Logs] --> P[Audit Trail]
    end
    
    subgraph "Configuration"
        Q[Environment Variables] --> R[Settings]
        R --> S[Key Management]
    end
    
    C -.->|On Failure| M
    I -.->|Metrics| K
    H -.->|Events| O
```

## Incident Response Flow

```mermaid
graph TD
    A[Rotation Failure Alert] --> B{Alert Type?}
    B -->|Lock Contention| C[Check Redis Connectivity]
    B -->|Key Promotion Failed| D[Verify Key Configuration]
    B -->|General Error| E[Check Celery Logs]
    
    C --> F{Redis OK?}
    F -->|Yes| G[Clear Stale Lock]
    F -->|No| H[Restart Redis Service]
    
    D --> I{Keys Valid?}
    I -->|Yes| J[Check Grace Period]
    I -->|No| K[Update Key Configuration]
    
    E --> L{Error Type?}
    L -->|Import Error| M[Check Dependencies]
    L -->|Permission Error| N[Verify File Permissions]
    L -->|Other| O[Review Error Details]
    
    G --> P[Restart Rotation Task]
    H --> P
    J --> P
    K --> P
    M --> P
    N --> P
    O --> P
    
    P --> Q[Verify Recovery]
    Q -->|Success| R[Monitor Metrics]
    Q -->|Failure| S[Escalate to Team]
    
    R --> T[Update Documentation]
    S --> T
```

## Monitoring Architecture

```mermaid
graph TD
    subgraph "Application Layer"
        A[JWT Rotation Task] --> B[Prometheus Client]
        A --> C[Slack Alerting]
        A --> D[Structured Logging]
    end
    
    subgraph "Monitoring Stack"
        B --> E[Prometheus Server]
        C --> F[Slack Webhook]
        D --> G[Log Aggregator]
        
        E --> H[Grafana Dashboards]
        E --> I[Alert Manager]
        G --> J[ELK Stack/Splunk]
    end
    
    subgraph "Operational Response"
        I --> K[PagerDuty/OpsGenie]
        F --> L[Slack Channel]
        H --> M[Operations Team]
    end
    
    K --> N[On-Call Engineer]
    L --> N
    M --> N
    
    N --> O[Incident Response]
    O --> P[Resolution]
    P --> Q[Post-Mortem]
```

## Key Rotation Timeline

```mermaid
gantt
    title JWT Key Rotation Timeline
    dateFormat  YYYY-MM-DD
    section Key A
    Active (Signing)    :a1, 2025-01-01, 30d
    Grace Period        :a2, after a1, 5d
    Retired             :a3, after a2, 1d
    
    section Key B
    Next Key            :b1, 2025-01-25, 5d
    Active (Signing)    :b2, after a1, 30d
    Grace Period        :b3, after b2, 5d
    Retired             :b4, after b3, 1d
    
    section Key C
    Next Key            :c1, 2025-02-20, 5d
    Active (Signing)    :c2, after b2, 30d
    Grace Period        :c3, after c2, 5d
    Retired             :c4, after c3, 1d
```

## Error Handling Flow

```mermaid
graph TD
    A[Rotation Task Starts] --> B{Acquire Lock?}
    B -->|No| C[Exit Gracefully]
    B -->|Yes| D[Execute Rotation Logic]
    
    D --> E{Logic Success?}
    E -->|Yes| F[Update Metrics]
    E -->|No| G[Handle Error]
    
    G --> H{Retryable Error?}
    H -->|Yes| I[Exponential Backoff]
    H -->|No| J[Send Alert]
    
    I --> K{Max Retries?}
    K -->|No| L[Retry Task]
    K -->|Yes| J
    
    L --> D
    J --> M[Log Error]
    F --> N[Release Lock]
    M --> N
    C --> O[Task Complete]
    N --> O
``` 
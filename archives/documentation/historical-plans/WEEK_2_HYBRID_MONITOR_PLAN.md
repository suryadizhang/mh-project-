# Week 2: Full Hybrid ThresholdMonitor - Implementation Plan

**Strategy:** Activity-Triggered Monitoring (Like a Gun Trigger 🔫)
**Efficiency:** 2,360 queries/day (96% reduction vs continuous polling)
**Detection Speed:** <1 second for active metrics
**Estimated Time:** 3-4 days

---

## 🎯 Core Concept: Trigger-Based Monitoring

```
NO API ACTIVITY (IDLE) 
    ↓
    😴 Sleep Mode
    - Check only CRITICAL rules every 5 minutes
    - Database availability, service health
    - Resource usage: 5%
    
    ↓ [API REQUEST DETECTED] 🔫 TRIGGER PULLED!
    
🔔 ACTIVE MODE
    ↓
    ✅ Wake up monitoring
    - Redis push notifications (instant detection)
    - Adaptive polling backup (safety net)
    - Check ALL enabled rules
    - Resource usage: 30%
    
    ↓ [5 MINUTES NO ACTIVITY]
    
😴 Back to IDLE (Gun safety on)
```

---

## 📋 Implementation Breakdown

### Week 2.1: MetricCollector Implementation

**Goal:** Gather metrics from all sources and store in Redis

**Components to Build:**

1. **Base MetricCollector Class**
```python
class MetricCollector:
    """Collects metrics from various sources"""
    
    def collect_system_metrics(self) -> Dict[str, float]:
        """CPU, memory, disk, network"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "network_sent_mb": psutil.net_io_counters().bytes_sent / 1024 / 1024,
        }
    
    def collect_database_metrics(self) -> Dict[str, float]:
        """Query duration, connection pool, locks"""
        return {
            "db_query_duration_avg_ms": self._get_avg_query_duration(),
            "db_connection_pool_usage": self._get_pool_usage(),
            "db_active_locks": self._get_active_locks(),
        }
    
    def collect_application_metrics(self) -> Dict[str, float]:
        """API response times, error rates"""
        return {
            "api_response_time_p95_ms": self._get_p95_response_time(),
            "api_error_rate_percent": self._get_error_rate(),
            "api_requests_per_second": self._get_request_rate(),
        }
    
    def collect_business_metrics(self) -> Dict[str, float]:
        """Booking rate, revenue, conversions"""
        return {
            "booking_conversion_rate": self._get_booking_rate(),
            "revenue_per_hour": self._get_revenue(),
            "active_users": self._get_active_users(),
        }
    
    def push_metric(self, metric_name: str, value: float):
        """Store metric in Redis and publish to channel"""
        # Store with 5-minute TTL
        self.redis.setex(f"metric:{metric_name}", 300, value)
        
        # Publish to subscribers
        self.redis.publish("metrics:updates", json.dumps({
            "metric_name": metric_name,
            "value": value,
            "timestamp": time.time()
        }))
```

2. **Integration Points**
   - System metrics: Hook into existing `system_health_monitor.py`
   - Database metrics: Query `pg_stat_statements`
   - Application metrics: Integrate with Prometheus metrics in `main.py`
   - Business metrics: Query application database

**Deliverables:**
- `monitoring/metric_collector.py` (~400 lines)
- Integration with existing monitoring systems
- Redis storage with TTL
- Pub/sub publishing

---

### Week 2.2: Activity-Based Wake/Sleep System

**Goal:** Implement trigger-based monitoring (like a gun trigger!)

**Components to Build:**

1. **Activity Detector Middleware**
```python
@app.middleware("http")
async def activity_detector_middleware(request: Request, call_next):
    """Detect ANY API activity and pull the trigger"""
    
    # PULL THE TRIGGER! 🔫
    monitoring_state.trigger_wake()
    
    # Update last activity timestamp
    redis.setex("monitor:last_activity", 600, time.time())
    
    response = await call_next(request)
    return response
```

2. **MonitoringState Manager**
```python
class MonitoringState:
    """Manages IDLE/ACTIVE state transitions"""
    
    STATES = ["IDLE", "ACTIVE", "ALERT"]
    
    def __init__(self):
        self.current_state = "IDLE"
        self.state_changed_at = datetime.utcnow()
        self.activity_timeout = 300  # 5 minutes
    
    def trigger_wake(self):
        """Pull the trigger - wake up monitoring"""
        if self.current_state == "IDLE":
            print("🔫 TRIGGER PULLED! Waking up monitor...")
            self.transition_to("ACTIVE")
    
    def check_should_sleep(self):
        """Check if we should go back to sleep"""
        last_activity = self._get_last_activity()
        time_since = time.time() - last_activity
        
        if time_since > self.activity_timeout:
            print("😴 No activity for 5+ minutes, going to sleep...")
            self.transition_to("IDLE")
            return True
        return False
    
    def transition_to(self, new_state: str):
        """State transition with logging"""
        old_state = self.current_state
        self.current_state = new_state
        self.state_changed_at = datetime.utcnow()
        
        print(f"🔄 State transition: {old_state} → {new_state}")
        
        # Store in Redis for distributed systems
        redis.set("monitor:state", new_state)
```

3. **State-Based Rule Selection**
```python
def get_rules_for_current_state(self):
    """Select which rules to check based on state"""
    
    if self.current_state == "IDLE":
        # Only critical rules
        return db.query(AlertRule).filter(
            AlertRule.is_enabled == True,
            AlertRule.priority == AlertPriority.CRITICAL
        ).all()
    
    elif self.current_state == "ACTIVE":
        # All enabled rules
        return db.query(AlertRule).filter(
            AlertRule.is_enabled == True
        ).all()
    
    elif self.current_state == "ALERT":
        # Alerting rules + critical
        return db.query(AlertRule).filter(
            AlertRule.is_enabled == True,
            or_(
                AlertRule.priority == AlertPriority.CRITICAL,
                AlertRule.id.in_(self.alerting_rule_ids)
            )
        ).all()
```

**Deliverables:**
- `monitoring/monitoring_state.py` (~300 lines)
- Activity detector middleware in `main.py`
- Redis-based state storage (for multi-instance deployments)
- State transition logging

---

### Week 2.3: Redis Push Notification System

**Goal:** Instant metric change detection via pub/sub

**Components to Build:**

1. **Redis Subscriber Task**
```python
@shared_task(bind=True)
def redis_metric_subscriber(self):
    """Listen to metric updates and check rules immediately"""
    
    redis = Redis()
    pubsub = redis.pubsub()
    pubsub.subscribe("metrics:updates")
    
    print("👂 Listening for metric updates...")
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                metric_name = data['metric_name']
                value = data['value']
                
                # Check rules for this specific metric
                db = next(get_db())
                monitor = ThresholdMonitor(db)
                
                rules = monitor.get_rules_for_metric(metric_name)
                for rule in rules:
                    monitor.check_single_rule(rule, current_value=value)
                
                db.close()
                
            except Exception as e:
                print(f"❌ Error processing metric update: {e}")
                # Don't break the listener loop
```

2. **Metric Push Helper**
```python
def push_metric_update(metric_name: str, value: float):
    """Helper to push metric updates from anywhere in the app"""
    
    redis = Redis()
    
    # Store metric
    redis.setex(f"metric:{metric_name}", 300, value)
    
    # Publish to subscribers
    redis.publish("metrics:updates", json.dumps({
        "metric_name": metric_name,
        "value": value,
        "timestamp": time.time()
    }))
    
    # Wake monitor if idle
    redis.setex("monitor:last_activity", 600, time.time())
```

3. **Integration Examples**
```python
# In API endpoint
@app.post("/api/bookings")
async def create_booking():
    start = time.time()
    result = do_booking()
    duration = (time.time() - start) * 1000  # ms
    
    # Push metric update (triggers immediate check)
    push_metric_update("api_response_time_ms", duration)
    
    return result

# In system monitor
def monitor_system():
    cpu = psutil.cpu_percent()
    push_metric_update("cpu_percent", cpu)
    
    memory = psutil.virtual_memory().percent
    push_metric_update("memory_percent", memory)
```

**Deliverables:**
- `monitoring/redis_subscriber.py` (~200 lines)
- `monitoring/metric_pusher.py` (~100 lines)
- Integration examples in documentation
- Celery task for subscriber

---

### Week 2.4: RuleEvaluator with State Tracking

**Goal:** Evaluate rules with duration checking and state persistence

**Components to Build:**

1. **RuleState Tracking**
```python
@dataclass
class RuleState:
    """Track rule evaluation state"""
    rule_id: int
    first_exceeded_at: Optional[datetime] = None
    is_over_threshold: bool = False
    last_checked_at: Optional[datetime] = None
    consecutive_violations: int = 0

class RuleEvaluator:
    """Evaluates rules and tracks state"""
    
    def __init__(self):
        self.rule_states: Dict[int, RuleState] = {}
    
    def evaluate_rule(
        self,
        rule: AlertRule,
        current_value: float
    ) -> Optional[AlertModel]:
        """
        Evaluate rule and return alert if triggered
        
        Returns:
            AlertModel if alert should be created, None otherwise
        """
        # Check threshold
        is_over = self._check_threshold(
            current_value,
            rule.operator,
            rule.threshold
        )
        
        # Get or create state
        state = self.rule_states.setdefault(
            rule.id,
            RuleState(rule_id=rule.id)
        )
        
        if is_over:
            if not state.is_over_threshold:
                # Just crossed threshold - START TIMER
                state.first_exceeded_at = datetime.utcnow()
                state.is_over_threshold = True
                state.consecutive_violations = 1
                print(f"⏱️ Rule '{rule.name}': Threshold exceeded, timer started")
            else:
                # Still over - CHECK DURATION
                state.consecutive_violations += 1
                elapsed = (datetime.utcnow() - state.first_exceeded_at).total_seconds()
                
                if elapsed >= rule.duration_seconds:
                    # Sustained for required duration
                    if self._check_cooldown(rule):
                        print(f"🚨 Rule '{rule.name}': Sustained for {elapsed:.0f}s, CREATING ALERT!")
                        
                        # Create alert via AlertService
                        alert = self._create_alert_from_rule(rule, current_value)
                        
                        # Update cooldown
                        rule.last_triggered_at = datetime.utcnow()
                        
                        return alert
                    else:
                        print(f"🔇 Rule '{rule.name}': In cooldown, skipping alert")
                else:
                    print(f"⏳ Rule '{rule.name}': Over for {elapsed:.0f}s/{rule.duration_seconds}s")
        else:
            # Back to normal - RESET
            if state.is_over_threshold:
                print(f"✅ Rule '{rule.name}': Back to normal, timer reset")
            state.first_exceeded_at = None
            state.is_over_threshold = False
            state.consecutive_violations = 0
        
        state.last_checked_at = datetime.utcnow()
        return None
    
    def _check_threshold(self, value: float, operator: str, threshold: float) -> bool:
        """Check if value meets threshold condition"""
        operators = {
            "gt": lambda v, t: v > t,
            "gte": lambda v, t: v >= t,
            "lt": lambda v, t: v < t,
            "lte": lambda v, t: v <= t,
            "eq": lambda v, t: v == t,
        }
        return operators[operator](value, threshold)
    
    def _check_cooldown(self, rule: AlertRule) -> bool:
        """Check if rule is in cooldown period"""
        if not rule.last_triggered_at:
            return True
        
        elapsed = (datetime.utcnow() - rule.last_triggered_at).total_seconds()
        return elapsed >= rule.cooldown_seconds
```

**Deliverables:**
- `monitoring/rule_evaluator.py` (~500 lines)
- State tracking with in-memory storage
- Duration verification logic
- Cooldown management
- Operator support (gt, gte, lt, lte, eq)

---

### Week 2.5: ThresholdMonitor Core Engine

**Goal:** Integrate all components into unified monitoring engine

**Components to Build:**

1. **Main ThresholdMonitor Class**
```python
class ThresholdMonitor:
    """
    Hybrid monitoring engine with:
    - Activity-based wake/sleep
    - Redis push notifications
    - Adaptive polling backup
    - State-based rule selection
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.redis = Redis()
        self.alert_service = AlertService(db)
        self.metric_collector = MetricCollector(db, redis)
        self.rule_evaluator = RuleEvaluator()
        self.monitoring_state = MonitoringState()
    
    def check_rules(self):
        """Main monitoring loop - called periodically"""
        
        # Check if should transition to sleep
        if self.monitoring_state.check_should_sleep():
            return  # Will only check critical rules
        
        # Get rules based on current state
        rules = self.monitoring_state.get_rules_for_current_state()
        
        print(f"🔍 Checking {len(rules)} rules in {self.monitoring_state.current_state} state")
        
        for rule in rules:
            self.check_single_rule(rule)
    
    def check_single_rule(
        self,
        rule: AlertRule,
        current_value: Optional[float] = None
    ):
        """Check a single rule"""
        
        # Get current metric value if not provided
        if current_value is None:
            current_value = self.metric_collector.get_metric_value(rule.metric_name)
        
        # Evaluate rule
        alert = self.rule_evaluator.evaluate_rule(rule, current_value)
        
        # Create alert if triggered
        if alert:
            self.db.add(alert)
            self.db.commit()
            print(f"✅ Alert created: {alert.title}")
```

2. **Adaptive Check Intervals**
```python
def get_check_interval(self, rule: AlertRule) -> int:
    """Get adaptive check interval based on state and priority"""
    
    state = self.rule_evaluator.rule_states.get(rule.id)
    
    # In ALERT state - check frequently
    if state and state.is_over_threshold:
        return 15  # 15 seconds
    
    # Based on priority
    intervals = {
        AlertPriority.CRITICAL: 30,   # 30 seconds
        AlertPriority.HIGH: 60,        # 1 minute
        AlertPriority.MEDIUM: 120,     # 2 minutes
        AlertPriority.LOW: 300,        # 5 minutes
    }
    
    return intervals.get(rule.priority, 120)
```

**Deliverables:**
- `monitoring/threshold_monitor.py` (~600 lines)
- Unified monitoring interface
- State machine integration
- Adaptive interval logic
- Error handling and logging

---

### Week 2.6: Celery Tasks & Background Jobs

**Goal:** Set up background tasks for continuous monitoring

**Components to Build:**

1. **Periodic Verification Task (Backup)**
```python
@shared_task(name="monitor_periodic_verification")
def periodic_verification_task():
    """
    Backup periodic check (safety net)
    Runs every 5 minutes regardless of state
    """
    db = next(get_db())
    try:
        monitor = ThresholdMonitor(db)
        
        # Always check critical rules
        critical_rules = monitor.get_critical_rules()
        for rule in critical_rules:
            monitor.check_single_rule(rule)
        
        # Check all rules if in ACTIVE state
        if monitor.monitoring_state.current_state == "ACTIVE":
            monitor.check_rules()
        
    except Exception as e:
        print(f"❌ Periodic verification error: {e}")
    finally:
        db.close()
```

2. **Metric Collection Task**
```python
@shared_task(name="monitor_collect_metrics")
def collect_metrics_task():
    """
    Collect metrics from all sources
    Runs every 30 seconds when ACTIVE, every 5 minutes when IDLE
    """
    redis = Redis()
    state = redis.get("monitor:state") or "IDLE"
    
    if state == "IDLE":
        # Only collect critical metrics
        metrics = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
        }
    else:
        # Collect all metrics
        collector = MetricCollector()
        metrics = collector.collect_all_metrics()
    
    # Push to Redis
    for metric_name, value in metrics.items():
        push_metric_update(metric_name, value)
```

3. **Celery Beat Schedule**
```python
# workers/celery_config.py

app.conf.beat_schedule = {
    # Periodic verification (backup)
    'monitor-periodic-verification': {
        'task': 'monitor_periodic_verification',
        'schedule': 300.0,  # Every 5 minutes
    },
    
    # Metric collection
    'monitor-collect-metrics': {
        'task': 'monitor_collect_metrics',
        'schedule': 30.0,  # Every 30 seconds
    },
    
    # State cleanup
    'monitor-cleanup-old-states': {
        'task': 'monitor_cleanup_states',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}
```

**Deliverables:**
- `workers/monitoring_tasks.py` (~400 lines)
- Celery Beat schedule configuration
- Task error handling and retries
- Logging and monitoring

---

### Week 2.7: API Endpoints for Rule Management

**Goal:** REST API for managing alert rules

**Components to Build:**

1. **Rule CRUD Endpoints**
```python
@router.post("/api/monitoring/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: CreateAlertRuleRequest,
    db: Session = Depends(get_db)
):
    """Create new alert rule"""
    db_rule = AlertRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    return db_rule

@router.get("/api/monitoring/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    is_enabled: Optional[bool] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List alert rules with filters"""
    query = db.query(AlertRule)
    if is_enabled is not None:
        query = query.filter(AlertRule.is_enabled == is_enabled)
    if priority:
        query = query.filter(AlertRule.priority == priority)
    return query.all()

@router.patch("/api/monitoring/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    updates: UpdateAlertRuleRequest,
    db: Session = Depends(get_db)
):
    """Update alert rule"""
    rule = db.query(AlertRule).get(rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found")
    
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(rule, key, value)
    
    db.commit()
    return rule

@router.delete("/api/monitoring/rules/{rule_id}")
async def delete_alert_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete alert rule"""
    rule = db.query(AlertRule).get(rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found")
    
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted"}
```

2. **Rule Testing Endpoint**
```python
@router.post("/api/monitoring/rules/{rule_id}/test")
async def test_alert_rule(
    rule_id: int,
    test_value: float,
    db: Session = Depends(get_db)
):
    """Test alert rule with a value"""
    rule = db.query(AlertRule).get(rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found")
    
    monitor = ThresholdMonitor(db)
    result = monitor.rule_evaluator.evaluate_rule(rule, test_value)
    
    return {
        "would_trigger": result is not None,
        "current_value": test_value,
        "threshold": rule.threshold,
        "operator": rule.operator,
        "duration_required": rule.duration_seconds,
    }
```

3. **Monitoring Status Endpoint**
```python
@router.get("/api/monitoring/status")
async def get_monitoring_status():
    """Get current monitoring status"""
    redis = Redis()
    
    return {
        "state": redis.get("monitor:state") or "IDLE",
        "last_activity": redis.get("monitor:last_activity"),
        "active_rules": db.query(AlertRule).filter(AlertRule.is_enabled == True).count(),
        "active_alerts": db.query(AlertModel).filter(AlertModel.status == "active").count(),
        "metrics_collected": redis.keys("metric:*"),
    }
```

**Deliverables:**
- `routers/monitoring.py` (~500 lines)
- Pydantic request/response models
- OpenAPI documentation
- Input validation

---

### Week 2.8: Testing & Validation

**Goal:** Comprehensive testing of hybrid monitoring system

**Test Coverage:**

1. **Unit Tests**
```python
# tests/monitoring/test_rule_evaluator.py
def test_rule_evaluation_over_threshold():
    """Test rule triggers when over threshold"""
    rule = AlertRule(
        metric_name="cpu_percent",
        operator="gt",
        threshold=80,
        duration_seconds=60
    )
    
    evaluator = RuleEvaluator()
    
    # First check - starts timer
    result = evaluator.evaluate_rule(rule, 90)
    assert result is None  # No alert yet
    
    # Simulate 60 seconds passing
    state = evaluator.rule_states[rule.id]
    state.first_exceeded_at = datetime.utcnow() - timedelta(seconds=61)
    
    # Second check - should trigger
    result = evaluator.evaluate_rule(rule, 90)
    assert result is not None
    assert result.title.contains("CPU")
```

2. **Integration Tests**
```python
# tests/monitoring/test_threshold_monitor_integration.py
def test_wake_sleep_cycle():
    """Test IDLE → ACTIVE → IDLE transition"""
    monitor = ThresholdMonitor(db)
    
    # Start in IDLE
    assert monitor.monitoring_state.current_state == "IDLE"
    
    # Simulate API activity
    monitor.monitoring_state.trigger_wake()
    assert monitor.monitoring_state.current_state == "ACTIVE"
    
    # Simulate 5 minutes no activity
    redis.delete("monitor:last_activity")
    monitor.monitoring_state.check_should_sleep()
    assert monitor.monitoring_state.current_state == "IDLE"
```

3. **Load Tests**
```python
# tests/monitoring/test_load.py
def test_high_metric_volume():
    """Test handling 1000 metric updates/second"""
    
    start = time.time()
    
    # Push 10,000 metrics
    for i in range(10000):
        push_metric_update(f"test_metric_{i % 10}", random.uniform(0, 100))
    
    duration = time.time() - start
    
    # Should handle 10k metrics in < 10 seconds
    assert duration < 10
    
    # All rules should still be evaluated
    alerts = db.query(AlertModel).filter(
        AlertModel.triggered_at > start_time
    ).all()
    
    assert len(alerts) > 0
```

**Deliverables:**
- Unit tests for each component (~20 tests)
- Integration tests for full flow (~10 tests)
- Load tests for performance validation (~5 tests)
- Test coverage report (target: >80%)

---

## 📊 Expected Resource Usage

### IDLE State (No API Activity)
```
Frequency: Every 5 minutes
Rules checked: 5 critical rules
Database queries: 5 * 2 = 10 queries per check
Daily queries (IDLE only): 10 * 12 * 24 = 2,880 queries

But IDLE is rare if you have any traffic at all!
```

### ACTIVE State (With API Activity)
```
Primary: Redis push notifications
- Triggered by actual metric changes
- ~50 metric updates/hour
- Database queries: 50 * 2 = 100 queries/hour
- Daily: 100 * 14 hours = 1,400 queries

Backup: Periodic verification
- Every 5 minutes
- All rules: 20 * 2 = 40 queries per check
- Daily: 40 * 12 * 14 hours = 6,720 queries

Total ACTIVE: 1,400 + 6,720 = 8,120 queries/day
```

### Total Daily (Mixed State)
```
Assuming:
- 14 hours ACTIVE (business hours with API traffic)
- 10 hours IDLE (night, low traffic)

ACTIVE: 1,400 + 960 (14h periodic) = 2,360 queries
IDLE: 600 queries (10h critical only)

Total: 2,960 queries/day

Compared to continuous polling: 63,360 queries/day
Savings: 95.3% reduction! ✨
```

---

## 🚀 Implementation Order

**Day 1:**
- ✅ Week 2.1: MetricCollector (integrate with existing monitoring)
- ✅ Week 2.2: Activity detector middleware + MonitoringState

**Day 2:**
- ✅ Week 2.3: Redis pub/sub subscriber
- ✅ Week 2.4: RuleEvaluator with state tracking

**Day 3:**
- ✅ Week 2.5: ThresholdMonitor core engine
- ✅ Week 2.6: Celery tasks setup

**Day 4:**
- ✅ Week 2.7: API endpoints
- ✅ Week 2.8: Testing & validation

---

## 🎯 Success Criteria

Week 2 is complete when:
- ✅ System automatically wakes on API activity
- ✅ Goes to sleep after 5 minutes no activity
- ✅ Alerts triggered correctly with duration checking
- ✅ Redis push notifications working for instant detection
- ✅ Periodic backup verification running
- ✅ API endpoints for rule management functional
- ✅ 80%+ test coverage
- ✅ < 3,000 database queries/day
- ✅ Sub-second alert detection for active metrics

---

## 📝 Notes

**Why Trigger-Based (Not Time-Based)?**
- ✅ More efficient - only monitor when needed
- ✅ Scales with traffic - low traffic = low overhead
- ✅ Immediate wake on activity - no delay
- ✅ Natural behavior - apps are active when users are active

**Trigger = Any API Request**
- User booking creation
- Admin dashboard access
- Health check endpoint (if you want)
- Any HTTP request to your backend

**Safety Nets:**
1. Critical rules checked even when IDLE
2. Periodic verification every 5 minutes (backup)
3. Redis push + polling (redundancy)

---

Ready to start Week 2.1? 🚀

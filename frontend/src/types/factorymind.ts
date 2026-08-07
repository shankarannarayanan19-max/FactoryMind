export type SeverityLevel = 'INFO' | 'WARNING' | 'CRITICAL' | 'SAFETY_BLOCK' | 'SUCCESS';
export type AssetHealth = 'NORMAL' | 'WARNING' | 'CRITICAL' | 'SENSOR_VALIDATION_REQUIRED';
export type OperationalState = 'RUNNING' | 'STOPPED' | 'UNKNOWN';
export type EnergyState = 'ENERGIZED' | 'DE_ENERGIZED' | 'UNKNOWN';
export type AccessState = 'CLOSED' | 'OPEN' | 'NORMAL';

export interface AgentState {
  id: string;
  name: string;
  location: string;
  room_name: string;
  confidence: number;
  battery: number;
  status: 'IDLE' | 'MOVING' | 'INSPECTING' | 'SAFETY_HALT' | 'EXECUTING';
  last_turn: number;
  active_tool?: string;
}

export interface RoomNode {
  id: string;
  name: string;
  code: string;
  x: number;
  y: number;
  description: string;
  exits: Record<string, string>;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL';
  assets: string[];
  sensors: string[];
  hazardsCount: number;
}

export interface AssetObject {
  id: string;
  name: string;
  type: string;
  room: string;
  operational_state: OperationalState;
  energy_state: EnergyState;
  access_state: AccessState;
  health_state: AssetHealth;
  confidence: number;
  last_observed_turn: number;
  aliases: string[];
  history: Array<{
    turn: number;
    state_key: string;
    old_value: any;
    new_value: any;
    raw_evidence?: string;
  }>;
  properties: Record<string, any>;
  relationships: Array<{
    relation: string;
    target: string;
  }>;
}

export interface SensorObject {
  id: string;
  name: string;
  type: string;
  sensor_type: 'TEMPERATURE' | 'VIBRATION' | 'PRESSURE' | 'CURRENT' | 'ACCESS';
  monitored_asset: string;
  unit: string;
  latest_value: number | null;
  status: AssetHealth;
  alarm?: string;
  history: Array<{
    turn: number;
    value: number;
    status: AssetHealth;
  }>;
}

export interface GraphRelationship {
  id: string;
  source: string;
  relation: string;
  target: string;
  status?: string;
  turn: number;
}

export interface DomainEvent {
  id: string;
  event_type: 
    | 'ROOM_ENTERED'
    | 'ASSET_DISCOVERED'
    | 'STATE_CHANGED'
    | 'ALARM_OBSERVED'
    | 'SAFETY_HAZARD_OBSERVED'
    | 'MEASUREMENT_RECORDED'
    | 'SENSOR_CONTRADICTION'
    | 'ANOMALY_CONFIRMED'
    | 'SHUTDOWN_REQUESTED'
    | 'INSPECTION_HOLD_PLACED'
    | 'MISSION_COMPLETED'
    | 'UNRESOLVED_ENTITY'
    | 'ASSET_HEALTH_DEGRADED';
  payload: Record<string, any>;
  severity: SeverityLevel;
  turn: number;
  timestamp: string;
}

export interface MemoryCard {
  id: string;
  type: 'OBSERVATION' | 'FACT' | 'RECONCILED_SNAPSHOT' | 'CONTRADICTION_RULE4' | 'ACTION_LOG';
  turn: number;
  title: string;
  summary: string;
  details: Record<string, any>;
  confidence: number;
  timestamp: string;
}

export interface MissionData {
  mission_id: string;
  title: string;
  target_asset: string;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'CRITICAL_HOLD' | 'FAILED';
  progress: number;
  score: number;
  safety_score: number;
  met_conditions: string[];
  missing_conditions: string[];
  recommended_information_need: string[];
  prohibited_actions: string[];
  start_time: string;
  turn_count: number;
}

export interface PipelineStep {
  name: 'Observe' | 'Analyze' | 'Reconcile' | 'Update World Model' | 'Plan' | 'Validate' | 'Execute' | 'Report';
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'BLOCKED';
  detail: string;
  duration_ms: number;
}

export interface ChatMessage {
  id: string;
  sender: 'USER' | 'FACTORYMIND_AI';
  text: string;
  timestamp: string;
  query_type?: 'LOCATION' | 'ABNORMALITY' | 'SAFETY' | 'GENERAL';
  source?: string;
  target_id?: string;
  target_room?: string;
  facts_json?: Record<string, any>;
}

export interface ScenarioTurnState {
  turn: number;
  action_name: string;
  command: string;
  room: string;
  observation: string;
  agent: AgentState;
  pipeline: PipelineStep[];
  assets: Record<string, AssetObject>;
  sensors: Record<string, SensorObject>;
  events: DomainEvent[];
  memories: MemoryCard[];
  mission: MissionData;
  telemetry_trends: Array<{
    turn: number;
    time: string;
    temperature: number;
    vibration: number;
  }>;
}

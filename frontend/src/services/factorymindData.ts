import type {
  AssetObject,
  ChatMessage,
  GraphRelationship,
  RoomNode,
  ScenarioTurnState,
  SensorObject
} from '../types/factorymind';

export const INITIAL_ROOMS: Record<string, RoomNode> = {
  'ROOM-PACK-01': {
    id: 'ROOM-PACK-01',
    name: 'Packaging Bay 1',
    code: 'BAY-01',
    x: 180,
    y: 160,
    description: 'Primary material packaging and conveyor transport line area.',
    exits: { east: 'ROOM-CTRL-01', south: 'ROOM-WEST-01' },
    status: 'CRITICAL',
    assets: ['CV-01', 'CV-M01', 'CV-M02', 'GUARD-CV01', 'PCS-CV01'],
    sensors: ['TS-CVM02-BRG', 'VS-CVM02'],
    hazardsCount: 2
  },
  'ROOM-CTRL-01': {
    id: 'ROOM-CTRL-01',
    name: 'Control Room 1',
    code: 'CTRL-01',
    x: 520,
    y: 160,
    description: 'Central SCADA monitoring station and portable tool storage depot.',
    exits: { west: 'ROOM-PACK-01', south: 'ROOM-EAST-01' },
    status: 'NORMAL',
    assets: ['TOOL-DEPOT-01'],
    sensors: ['ENV-CTRL-TEMP'],
    hazardsCount: 0
  },
  'ROOM-WEST-01': {
    id: 'ROOM-WEST-01',
    name: 'Motor Access Sub-Gallery',
    code: 'SUB-W1',
    x: 180,
    y: 420,
    description: 'Lower auxiliary gallery providing physical access to conveyor tail drive assemblies.',
    exits: { north: 'ROOM-PACK-01', east: 'ROOM-EAST-01' },
    status: 'WARNING',
    assets: ['PUMP-AUX-01'],
    sensors: ['PS-AUX-01'],
    hazardsCount: 1
  },
  'ROOM-EAST-01': {
    id: 'ROOM-EAST-01',
    name: 'High Voltage Switchgear Vault',
    code: 'VAULT-E1',
    x: 520,
    y: 420,
    description: '33kV main transformer bay and primary conveyor MCC panel.',
    exits: { north: 'ROOM-CTRL-01', west: 'ROOM-WEST-01' },
    status: 'NORMAL',
    assets: ['MCC-CV01'],
    sensors: ['VOLT-MCC-01'],
    hazardsCount: 0
  }
};

export const INITIAL_ASSETS: Record<string, AssetObject> = {
  'CV-01': {
    id: 'CV-01',
    name: 'Conveyor Line 1',
    type: 'CONVEYOR',
    room: 'ROOM-PACK-01',
    operational_state: 'RUNNING',
    energy_state: 'ENERGIZED',
    access_state: 'NORMAL',
    health_state: 'WARNING',
    confidence: 0.99,
    last_observed_turn: 2,
    aliases: ['conveyor line 1', 'cv-01', 'main conveyor'],
    history: [
      { turn: 1, state_key: 'operational_state', old_value: 'UNKNOWN', new_value: 'RUNNING', raw_evidence: 'Conveyor Line 1 (CV-01) is active' },
      { turn: 6, state_key: 'operational_state', old_value: 'RUNNING', new_value: 'STOPPED', raw_evidence: 'Conveyor Line 1 (CV-01) operational state is STOPPED' },
      { turn: 6, state_key: 'energy_state', old_value: 'ENERGIZED', new_value: 'DE_ENERGIZED', raw_evidence: 'Energy state is DE_ENERGIZED' }
    ],
    properties: { speed_m_s: 1.8, belt_width_mm: 1200, length_m: 45 },
    relationships: [{ relation: 'located_in', target: 'ROOM-PACK-01' }]
  },
  'CV-M01': {
    id: 'CV-M01',
    name: 'Main Drive Motor',
    type: 'MOTOR',
    room: 'ROOM-PACK-01',
    operational_state: 'RUNNING',
    energy_state: 'ENERGIZED',
    access_state: 'NORMAL',
    health_state: 'NORMAL',
    confidence: 0.98,
    last_observed_turn: 2,
    aliases: ['main drive motor', 'cv-m01'],
    history: [],
    properties: { power_kW: 75, rpm: 1480, voltage: 400 },
    relationships: [
      { relation: 'part_of', target: 'CV-01' },
      { relation: 'located_in', target: 'ROOM-PACK-01' }
    ]
  },
  'CV-M02': {
    id: 'CV-M02',
    name: 'Tail Drive Motor & Bearing Assembly',
    type: 'MOTOR',
    room: 'ROOM-PACK-01',
    operational_state: 'RUNNING',
    energy_state: 'ENERGIZED',
    access_state: 'NORMAL',
    health_state: 'CRITICAL',
    confidence: 0.99,
    last_observed_turn: 3,
    aliases: ['tail drive motor', 'tail motor', 'm02', 'cv-m02'],
    history: [
      { turn: 4, state_key: 'health_state', old_value: 'NORMAL', new_value: 'WARNING', raw_evidence: 'TS-CVM02-BRG reading 82.0 C exceeds threshold 70.0 C' },
      { turn: 5, state_key: 'health_state', old_value: 'WARNING', new_value: 'CRITICAL', raw_evidence: 'VS-CVM02 reading 5.8 mm/s exceeds critical limit 4.5 mm/s' }
    ],
    properties: { power_kW: 45, bearing_model: 'SKF-22216-E', grease_type: 'Polyrex-EM' },
    relationships: [
      { relation: 'part_of', target: 'CV-01' },
      { relation: 'located_in', target: 'ROOM-PACK-01' }
    ]
  },
  'GUARD-CV01': {
    id: 'GUARD-CV01',
    name: 'Conveyor Safety Guard',
    type: 'GUARD',
    room: 'ROOM-PACK-01',
    operational_state: 'UNKNOWN',
    energy_state: 'UNKNOWN',
    access_state: 'CLOSED',
    health_state: 'NORMAL',
    confidence: 1.0,
    last_observed_turn: 1,
    aliases: ['conveyor guard', 'guard-cv01', 'safety cage'],
    history: [
      { turn: 8, state_key: 'access_state', old_value: 'CLOSED', new_value: 'OPEN', raw_evidence: 'Access state is now OPEN' }
    ],
    properties: { interlocked: true, safety_rating: 'Category-4 SIL3' },
    relationships: [
      { relation: 'protects', target: 'CV-01' },
      { relation: 'located_in', target: 'ROOM-PACK-01' }
    ]
  },
  'PCS-CV01': {
    id: 'PCS-CV01',
    name: 'PLC Control Cabinet CV-01',
    type: 'PLC',
    room: 'ROOM-PACK-01',
    operational_state: 'RUNNING',
    energy_state: 'ENERGIZED',
    access_state: 'CLOSED',
    health_state: 'NORMAL',
    confidence: 0.99,
    last_observed_turn: 2,
    aliases: ['plc control cabinet', 'pcs-cv01', 'control panel'],
    history: [],
    properties: { controller: 'Siemens S7-1500', firmware: 'v2.9.4', ip: '192.168.10.15' },
    relationships: [
      { relation: 'controls', target: 'CV-01' },
      { relation: 'located_in', target: 'ROOM-PACK-01' }
    ]
  }
};

export const INITIAL_SENSORS: Record<string, SensorObject> = {
  'TS-CVM02-BRG': {
    id: 'TS-CVM02-BRG',
    name: 'Tail Bearing Temp Sensor',
    type: 'SENSOR',
    sensor_type: 'TEMPERATURE',
    monitored_asset: 'CV-M02',
    unit: 'C',
    latest_value: 82.0,
    status: 'CRITICAL',
    alarm: 'ELEVATED_TEMPERATURE_WARNING',
    history: [
      { turn: 1, value: 42.0, status: 'NORMAL' },
      { turn: 4, value: 82.0, status: 'CRITICAL' }
    ]
  },
  'VS-CVM02': {
    id: 'VS-CVM02',
    name: 'Tail Motor Vibration Sensor',
    type: 'SENSOR',
    sensor_type: 'VIBRATION',
    monitored_asset: 'CV-M02',
    unit: 'mm/s',
    latest_value: 5.8,
    status: 'CRITICAL',
    alarm: 'SEVERE_VIBRATION_ALARM',
    history: [
      { turn: 1, value: 1.2, status: 'NORMAL' },
      { turn: 5, value: 5.8, status: 'CRITICAL' }
    ]
  }
};

export const CANONICAL_TURNS: ScenarioTurnState[] = [
  {
    turn: 1,
    action_name: 'Initial Reset & Room Scan',
    command: 'look',
    room: 'ROOM-PACK-01',
    observation: 'You are standing in Packaging Bay 1 (ROOM-PACK-01). You see Conveyor Line 1 (CV-01), Tail Drive Motor (CV-M02), Temperature Sensor (TS-CVM02-BRG), and Vibration Sensor (VS-CVM02). Exits lead east to Control Room 1.',
    agent: {
      id: 'AGENT-01',
      name: 'Inspection Unit Zero',
      location: 'ROOM-PACK-01',
      room_name: 'Packaging Bay 1',
      confidence: 1.0,
      battery: 98,
      status: 'INSPECTING',
      last_turn: 1
    },
    pipeline: [
      { name: 'Observe', status: 'COMPLETED', detail: 'Scanned Packaging Bay 1 environment', duration_ms: 12 },
      { name: 'Analyze', status: 'COMPLETED', detail: 'Parsed room boundaries & visible asset tags', duration_ms: 8 },
      { name: 'Reconcile', status: 'COMPLETED', detail: 'Updated agent location to ROOM-PACK-01', duration_ms: 15 },
      { name: 'Update World Model', status: 'COMPLETED', detail: 'Persisted room entities into graph snapshot', duration_ms: 10 },
      { name: 'Plan', status: 'COMPLETED', detail: 'Proposed inspection of conveyor line CV-01', duration_ms: 6 },
      { name: 'Validate', status: 'COMPLETED', detail: 'Action look authorized', duration_ms: 4 },
      { name: 'Execute', status: 'COMPLETED', detail: 'Command look executed cleanly', duration_ms: 18 },
      { name: 'Report', status: 'COMPLETED', detail: 'Level 1 command echo generated', duration_ms: 5 }
    ],
    assets: INITIAL_ASSETS,
    sensors: {
      'TS-CVM02-BRG': { ...INITIAL_SENSORS['TS-CVM02-BRG'], latest_value: 45.0, status: 'NORMAL' },
      'VS-CVM02': { ...INITIAL_SENSORS['VS-CVM02'], latest_value: 1.2, status: 'NORMAL' }
    },
    events: [
      {
        id: 'EVT-101',
        event_type: 'ROOM_ENTERED',
        payload: { room: 'ROOM-PACK-01', previous_room: 'UNKNOWN' },
        severity: 'INFO',
        turn: 1,
        timestamp: '01:38:00'
      },
      {
        id: 'EVT-102',
        event_type: 'ASSET_DISCOVERED',
        payload: { asset_id: 'CV-01', room: 'ROOM-PACK-01' },
        severity: 'INFO',
        turn: 1,
        timestamp: '01:38:01'
      }
    ],
    memories: [
      {
        id: 'MEM-101',
        type: 'OBSERVATION',
        turn: 1,
        title: 'Room Scan: Packaging Bay 1',
        summary: 'Detected 5 primary assets and 2 telemetry sensors in Packaging Bay 1.',
        details: { room: 'ROOM-PACK-01', assets_found: 5 },
        confidence: 1.0,
        timestamp: '01:38:02'
      }
    ],
    mission: {
      mission_id: 'MIS-CV01-INSPECT',
      title: 'Inspect CV-M02 Overheating & Vibration Alarm',
      target_asset: 'CV-M02',
      status: 'IN_PROGRESS',
      progress: 0.15,
      score: 85,
      safety_score: 100,
      met_conditions: ['room_scanned'],
      missing_conditions: ['independent_temperature_measurement', 'safety_shutdown_verified', 'final_report_generated'],
      recommended_information_need: [],
      prohibited_actions: ['remove_guard_while_running'],
      start_time: '2026-08-07 01:38:00',
      turn_count: 1
    },
    telemetry_trends: [
      { turn: 1, time: '01:38:00', temperature: 45.0, vibration: 1.2 }
    ]
  },
  {
    turn: 4,
    action_name: 'Fixed Sensor Reading (TS-CVM02-BRG)',
    command: 'read TS-CVM02-BRG',
    room: 'ROOM-PACK-01',
    observation: 'Temperature Sensor (TS-CVM02-BRG) reading is 82.0 C. Threshold normal max: 70.0 C. Status: WARNING / ALARM.',
    agent: {
      id: 'AGENT-01',
      name: 'Inspection Unit Zero',
      location: 'ROOM-PACK-01',
      room_name: 'Packaging Bay 1',
      confidence: 1.0,
      battery: 95,
      status: 'INSPECTING',
      last_turn: 4
    },
    pipeline: [
      { name: 'Observe', status: 'COMPLETED', detail: 'Read fixed bearing telemetry TS-CVM02-BRG', duration_ms: 14 },
      { name: 'Analyze', status: 'COMPLETED', detail: 'Extracted value 82.0 C & evaluated threshold rules', duration_ms: 9 },
      { name: 'Reconcile', status: 'COMPLETED', detail: 'Emitted THRESHOLD_BREACH & ASSET_HEALTH_DEGRADED', duration_ms: 18 },
      { name: 'Update World Model', status: 'COMPLETED', detail: 'Set CV-M02 health_state to WARNING', duration_ms: 11 },
      { name: 'Plan', status: 'COMPLETED', detail: 'Identified missing independent pyrometer evidence (§13)', duration_ms: 7 },
      { name: 'Validate', status: 'COMPLETED', detail: 'Read sensor command validated', duration_ms: 5 },
      { name: 'Execute', status: 'COMPLETED', detail: 'Telemetry record stored', duration_ms: 16 },
      { name: 'Report', status: 'COMPLETED', detail: 'Level 2 state snapshot updated', duration_ms: 6 }
    ],
    assets: {
      ...INITIAL_ASSETS,
      'CV-M02': { ...INITIAL_ASSETS['CV-M02'], health_state: 'WARNING' }
    },
    sensors: {
      ...INITIAL_SENSORS,
      'TS-CVM02-BRG': { ...INITIAL_SENSORS['TS-CVM02-BRG'], latest_value: 82.0, status: 'WARNING', alarm: 'ELEVATED_TEMPERATURE' }
    },
    events: [
      {
        id: 'EVT-401',
        event_type: 'MEASUREMENT_RECORDED',
        payload: { sensor_id: 'TS-CVM02-BRG', value: 82.0, unit: 'C', status: 'WARNING' },
        severity: 'WARNING',
        turn: 4,
        timestamp: '01:41:10'
      },
      {
        id: 'EVT-402',
        event_type: 'ALARM_OBSERVED',
        payload: { sensor_id: 'TS-CVM02-BRG', monitored_asset: 'CV-M02', status: 'WARNING' },
        severity: 'WARNING',
        turn: 4,
        timestamp: '01:41:11'
      },
      {
        id: 'EVT-403',
        event_type: 'ASSET_HEALTH_DEGRADED',
        payload: { asset_id: 'CV-M02', old_health_state: 'NORMAL', new_health_state: 'WARNING' },
        severity: 'WARNING',
        turn: 4,
        timestamp: '01:41:12'
      }
    ],
    memories: [
      {
        id: 'MEM-401',
        type: 'FACT',
        turn: 4,
        title: 'Thermal Breach Detected',
        summary: 'Fixed sensor TS-CVM02-BRG recorded 82.0 C (exceeds 70.0 C normal limit).',
        details: { asset: 'CV-M02', temperature: 82.0, status: 'WARNING' },
        confidence: 0.99,
        timestamp: '01:41:15'
      }
    ],
    mission: {
      mission_id: 'MIS-CV01-INSPECT',
      title: 'Inspect CV-M02 Overheating & Vibration Alarm',
      target_asset: 'CV-M02',
      status: 'IN_PROGRESS',
      progress: 0.45,
      score: 88,
      safety_score: 100,
      met_conditions: ['room_scanned', 'sensor_data_reconciled'],
      missing_conditions: ['independent_temperature_measurement', 'safety_shutdown_verified', 'final_report_generated'],
      recommended_information_need: ['independent_temperature_measurement', 'remove_guard_for_direct_measurement'],
      prohibited_actions: ['remove_guard_while_running'],
      start_time: '2026-08-07 01:38:00',
      turn_count: 4
    },
    telemetry_trends: [
      { turn: 1, time: '01:38:00', temperature: 45.0, vibration: 1.2 },
      { turn: 2, time: '01:39:00', temperature: 52.0, vibration: 1.5 },
      { turn: 3, time: '01:40:00', temperature: 68.0, vibration: 2.1 },
      { turn: 4, time: '01:41:00', temperature: 82.0, vibration: 3.4 }
    ]
  },
  {
    turn: 5,
    action_name: 'Safety Rule Gate (SR-GUARD-REMOVE Block)',
    command: 'remove GUARD-CV01',
    room: 'ROOM-PACK-01',
    observation: 'SAFETY BLOCK TRIGGERED! Rule SR-GUARD-REMOVE: Conveyor Line 1 (CV-01) is currently RUNNING and ENERGIZED. Protective guard GUARD-CV01 cannot be removed while conveyor is running. Rerecommended action: request shutdown of CV-01.',
    agent: {
      id: 'AGENT-01',
      name: 'Inspection Unit Zero',
      location: 'ROOM-PACK-01',
      room_name: 'Packaging Bay 1',
      confidence: 1.0,
      battery: 92,
      status: 'SAFETY_HALT',
      last_turn: 5
    },
    pipeline: [
      { name: 'Observe', status: 'COMPLETED', detail: 'Received user/planner command to remove GUARD-CV01', duration_ms: 10 },
      { name: 'Analyze', status: 'COMPLETED', detail: 'Evaluated physical access prerequisites', duration_ms: 8 },
      { name: 'Reconcile', status: 'COMPLETED', detail: 'Cross-checked CV-01 operational_state (RUNNING)', duration_ms: 12 },
      { name: 'Update World Model', status: 'COMPLETED', detail: 'Logged safety verification check', duration_ms: 9 },
      { name: 'Plan', status: 'COMPLETED', detail: 'Pivoted goal to safety mitigation shutdown request', duration_ms: 14 },
      { name: 'Validate', status: 'BLOCKED', detail: 'BLOCKED by Rule SR-GUARD-REMOVE (Machinery Running)', duration_ms: 6 },
      { name: 'Execute', status: 'BLOCKED', detail: 'Action halted by Safety Validator', duration_ms: 2 },
      { name: 'Report', status: 'COMPLETED', detail: 'Generated safety block alert and allowed next actions', duration_ms: 7 }
    ],
    assets: {
      ...INITIAL_ASSETS,
      'CV-M02': { ...INITIAL_ASSETS['CV-M02'], health_state: 'CRITICAL' }
    },
    sensors: {
      ...INITIAL_SENSORS,
      'TS-CVM02-BRG': { ...INITIAL_SENSORS['TS-CVM02-BRG'], latest_value: 82.0, status: 'CRITICAL' },
      'VS-CVM02': { ...INITIAL_SENSORS['VS-CVM02'], latest_value: 5.8, status: 'CRITICAL' }
    },
    events: [
      {
        id: 'EVT-501',
        event_type: 'SAFETY_HAZARD_OBSERVED',
        payload: { rule_id: 'SR-GUARD-REMOVE', asset: 'CV-01', operational_state: 'RUNNING' },
        severity: 'SAFETY_BLOCK',
        turn: 5,
        timestamp: '01:42:05'
      }
    ],
    memories: [
      {
        id: 'MEM-501',
        type: 'FACT',
        turn: 5,
        title: 'Safety Interlock Engaged',
        summary: 'Attempted guard removal blocked because CV-01 is ENERGIZED. Precondition requires DE_ENERGIZED.',
        details: { rule_id: 'SR-GUARD-REMOVE', allowed_next_actions: ['request shutdown of CV-01'] },
        confidence: 1.0,
        timestamp: '01:42:08'
      }
    ],
    mission: {
      mission_id: 'MIS-CV01-INSPECT',
      title: 'Inspect CV-M02 Overheating & Vibration Alarm',
      target_asset: 'CV-M02',
      status: 'CRITICAL_HOLD',
      progress: 0.60,
      score: 92,
      safety_score: 100,
      met_conditions: ['room_scanned', 'sensor_data_reconciled', 'safety_block_mitigated'],
      missing_conditions: ['safety_shutdown_verified', 'independent_temperature_measurement', 'final_report_generated'],
      recommended_information_need: ['request_shutdown_of_cv01', 'independent_temperature_measurement'],
      prohibited_actions: ['remove_guard_while_running'],
      start_time: '2026-08-07 01:38:00',
      turn_count: 5
    },
    telemetry_trends: [
      { turn: 1, time: '01:38:00', temperature: 45.0, vibration: 1.2 },
      { turn: 2, time: '01:39:00', temperature: 52.0, vibration: 1.5 },
      { turn: 3, time: '01:40:00', temperature: 68.0, vibration: 2.1 },
      { turn: 4, time: '01:41:00', temperature: 82.0, vibration: 3.4 },
      { turn: 5, time: '01:42:00', temperature: 82.0, vibration: 5.8 }
    ]
  },
  {
    turn: 6,
    action_name: 'Conveyor Shutdown Request',
    command: 'request shutdown of CV-01',
    room: 'ROOM-PACK-01',
    observation: 'Shutdown request authorized by safety protocol SR-SHUTDOWN-REQUEST. Conveyor Line 1 (CV-01) operational state updated to STOPPED. Energy state updated to DE_ENERGIZED. PLC Panel PCS-CV01 status: STOPPED.',
    agent: {
      id: 'AGENT-01',
      name: 'Inspection Unit Zero',
      location: 'ROOM-PACK-01',
      room_name: 'Packaging Bay 1',
      confidence: 1.0,
      battery: 90,
      status: 'EXECUTING',
      last_turn: 6
    },
    pipeline: [
      { name: 'Observe', status: 'COMPLETED', detail: 'Issued shutdown request command for CV-01', duration_ms: 11 },
      { name: 'Analyze', status: 'COMPLETED', detail: 'Verified authorization rule SR-SHUTDOWN-REQUEST', duration_ms: 6 },
      { name: 'Reconcile', status: 'COMPLETED', detail: 'Updated operational_state -> STOPPED & energy_state -> DE_ENERGIZED', duration_ms: 17 },
      { name: 'Update World Model', status: 'COMPLETED', detail: 'Emitted SHUTDOWN_REQUESTED & STATE_CHANGED events', duration_ms: 14 },
      { name: 'Plan', status: 'COMPLETED', detail: 'Preconditions cleared for GUARD-CV01 removal', duration_ms: 8 },
      { name: 'Validate', status: 'COMPLETED', detail: 'Shutdown action approved', duration_ms: 4 },
      { name: 'Execute', status: 'COMPLETED', detail: 'Pipelined PLC trip signal to PCS-CV01', duration_ms: 22 },
      { name: 'Report', status: 'COMPLETED', detail: 'Updated mission progress to 80%', duration_ms: 5 }
    ],
    assets: {
      ...INITIAL_ASSETS,
      'CV-01': { ...INITIAL_ASSETS['CV-01'], operational_state: 'STOPPED', energy_state: 'DE_ENERGIZED' },
      'CV-M01': { ...INITIAL_ASSETS['CV-M01'], operational_state: 'STOPPED', energy_state: 'DE_ENERGIZED' },
      'CV-M02': { ...INITIAL_ASSETS['CV-M02'], operational_state: 'STOPPED', energy_state: 'DE_ENERGIZED', health_state: 'CRITICAL' },
      'PCS-CV01': { ...INITIAL_ASSETS['PCS-CV01'], operational_state: 'STOPPED', energy_state: 'DE_ENERGIZED' }
    },
    sensors: INITIAL_SENSORS,
    events: [
      {
        id: 'EVT-601',
        event_type: 'SHUTDOWN_REQUESTED',
        payload: { asset_id: 'CV-01', turn: 6 },
        severity: 'WARNING',
        turn: 6,
        timestamp: '01:43:00'
      },
      {
        id: 'EVT-602',
        event_type: 'STATE_CHANGED',
        payload: { entity_id: 'CV-01', state_key: 'operational_state', value: 'STOPPED' },
        severity: 'INFO',
        turn: 6,
        timestamp: '01:43:01'
      }
    ],
    memories: [
      {
        id: 'MEM-601',
        type: 'RECONCILED_SNAPSHOT',
        turn: 6,
        title: 'Conveyor Line De-Energized',
        summary: 'CV-01 successfully brought to STOPPED and DE_ENERGIZED state via PLC override.',
        details: { asset: 'CV-01', operational_state: 'STOPPED', energy_state: 'DE_ENERGIZED' },
        confidence: 1.0,
        timestamp: '01:43:05'
      }
    ],
    mission: {
      mission_id: 'MIS-CV01-INSPECT',
      title: 'Inspect CV-M02 Overheating & Vibration Alarm',
      target_asset: 'CV-M02',
      status: 'IN_PROGRESS',
      progress: 0.80,
      score: 95,
      safety_score: 100,
      met_conditions: ['room_scanned', 'sensor_data_reconciled', 'safety_shutdown_verified'],
      missing_conditions: ['independent_temperature_measurement', 'final_report_generated'],
      recommended_information_need: ['remove_guard_for_direct_measurement'],
      prohibited_actions: [],
      start_time: '2026-08-07 01:38:00',
      turn_count: 6
    },
    telemetry_trends: [
      { turn: 1, time: '01:38:00', temperature: 45.0, vibration: 1.2 },
      { turn: 2, time: '01:39:00', temperature: 52.0, vibration: 1.5 },
      { turn: 3, time: '01:40:00', temperature: 68.0, vibration: 2.1 },
      { turn: 4, time: '01:41:00', temperature: 82.0, vibration: 3.4 },
      { turn: 5, time: '01:42:00', temperature: 82.0, vibration: 5.8 },
      { turn: 6, time: '01:43:00', temperature: 74.0, vibration: 0.2 }
    ]
  },
  {
    turn: 8,
    action_name: 'Guard Removal & Direct Pyrometer Measurement',
    command: 'remove GUARD-CV01',
    room: 'ROOM-PACK-01',
    observation: 'Interlocked Safety Guard (GUARD-CV01) access state is now OPEN. Direct surface measurement taken on CV-M02 bearing housing with infrared_pyrometer: 48.0 C. Fixed sensor reads 82.0 C. Rule 4 Contradiction detected! Status set to SENSOR_VALIDATION_REQUIRED.',
    agent: {
      id: 'AGENT-01',
      name: 'Inspection Unit Zero',
      location: 'ROOM-PACK-01',
      room_name: 'Packaging Bay 1',
      confidence: 1.0,
      battery: 88,
      status: 'INSPECTING',
      last_turn: 8,
      active_tool: 'infrared_pyrometer'
    },
    pipeline: [
      { name: 'Observe', status: 'COMPLETED', detail: 'Removed GUARD-CV01 and took portable pyrometer measurement', duration_ms: 16 },
      { name: 'Analyze', status: 'COMPLETED', detail: 'Compared portable 48.0 C vs fixed telemetry 82.0 C', duration_ms: 12 },
      { name: 'Reconcile', status: 'COMPLETED', detail: 'Reconciliation Rule 4 triggered: Created CONTRADICTS relation', duration_ms: 21 },
      { name: 'Update World Model', status: 'COMPLETED', detail: 'Set TS-CVM02-BRG status to SENSOR_VALIDATION_REQUIRED (No Averaging)', duration_ms: 15 },
      { name: 'Plan', status: 'COMPLETED', detail: 'All missing evidence gathered; generating final Level 4 report', duration_ms: 9 },
      { name: 'Validate', status: 'COMPLETED', detail: 'Direct tool measurement validated with OPEN guard', duration_ms: 5 },
      { name: 'Execute', status: 'COMPLETED', detail: 'Completed direct contact measurement', duration_ms: 19 },
      { name: 'Report', status: 'COMPLETED', detail: 'Generated Level 4 Final Structured Mission Report', duration_ms: 14 }
    ],
    assets: {
      ...INITIAL_ASSETS,
      'CV-01': { ...INITIAL_ASSETS['CV-01'], operational_state: 'STOPPED', energy_state: 'DE_ENERGIZED' },
      'CV-M02': { ...INITIAL_ASSETS['CV-M02'], operational_state: 'STOPPED', energy_state: 'DE_ENERGIZED', health_state: 'CRITICAL' },
      'GUARD-CV01': { ...INITIAL_ASSETS['GUARD-CV01'], access_state: 'OPEN' }
    },
    sensors: {
      ...INITIAL_SENSORS,
      'TS-CVM02-BRG': {
        ...INITIAL_SENSORS['TS-CVM02-BRG'],
        latest_value: 82.0,
        status: 'SENSOR_VALIDATION_REQUIRED',
        alarm: 'CONTRADICTION_WITH_PORTABLE_PYROMETER'
      }
    },
    events: [
      {
        id: 'EVT-801',
        event_type: 'SENSOR_CONTRADICTION',
        payload: {
          fixed_sensor_id: 'TS-CVM02-BRG',
          portable_tool_id: 'infrared_pyrometer',
          fixed_value: 82.0,
          portable_value: 48.0,
          monitored_asset: 'CV-M02',
          status: 'SENSOR_VALIDATION_REQUIRED'
        },
        severity: 'WARNING',
        turn: 8,
        timestamp: '01:45:00'
      },
      {
        id: 'EVT-802',
        event_type: 'ANOMALY_CONFIRMED',
        payload: { asset_id: 'CV-M02', defect: 'Bearing degradation & sensor drift' },
        severity: 'CRITICAL',
        turn: 8,
        timestamp: '01:45:02'
      },
      {
        id: 'EVT-803',
        event_type: 'MISSION_COMPLETED',
        payload: { mission_id: 'MIS-CV01-INSPECT', status: 'COMPLETED' },
        severity: 'INFO',
        turn: 8,
        timestamp: '01:45:05'
      }
    ],
    memories: [
      {
        id: 'MEM-801',
        type: 'CONTRADICTION_RULE4',
        turn: 8,
        title: 'Rule 4 Sensor Contradiction Registered',
        summary: 'Portable pyrometer (48.0 C) contradicts fixed sensor TS-CVM02-BRG (82.0 C). Fixed sensor set to SENSOR_VALIDATION_REQUIRED without averaging.',
        details: { fixed_val: 82.0, portable_val: 48.0, asset: 'CV-M02', rule: 'Rule 4 (No Averaging)' },
        confidence: 1.0,
        timestamp: '01:45:10'
      }
    ],
    mission: {
      mission_id: 'MIS-CV01-INSPECT',
      title: 'Inspect CV-M02 Overheating & Vibration Alarm',
      target_asset: 'CV-M02',
      status: 'COMPLETED',
      progress: 1.0,
      score: 98,
      safety_score: 100,
      met_conditions: ['room_scanned', 'sensor_data_reconciled', 'safety_shutdown_verified', 'independent_temperature_measurement', 'final_report_generated'],
      missing_conditions: [],
      recommended_information_need: [],
      prohibited_actions: [],
      start_time: '2026-08-07 01:38:00',
      turn_count: 8
    },
    telemetry_trends: [
      { turn: 1, time: '01:38:00', temperature: 45.0, vibration: 1.2 },
      { turn: 2, time: '01:39:00', temperature: 52.0, vibration: 1.5 },
      { turn: 3, time: '01:40:00', temperature: 68.0, vibration: 2.1 },
      { turn: 4, time: '01:41:00', temperature: 82.0, vibration: 3.4 },
      { turn: 5, time: '01:42:00', temperature: 82.0, vibration: 5.8 },
      { turn: 6, time: '01:43:00', temperature: 74.0, vibration: 0.2 },
      { turn: 7, time: '01:44:00', temperature: 65.0, vibration: 0.1 },
      { turn: 8, time: '01:45:00', temperature: 48.0, vibration: 0.1 }
    ]
  }
];

export const INITIAL_RELATIONSHIPS: GraphRelationship[] = [
  { id: 'rel-1', source: 'CV-M01', relation: 'part_of', target: 'CV-01', turn: 0 },
  { id: 'rel-2', source: 'CV-M02', relation: 'part_of', target: 'CV-01', turn: 0 },
  { id: 'rel-3', source: 'GUARD-CV01', relation: 'protects', target: 'CV-01', turn: 0 },
  { id: 'rel-4', source: 'PCS-CV01', relation: 'controls', target: 'CV-01', turn: 0 },
  { id: 'rel-5', source: 'TS-CVM02-BRG', relation: 'monitors', target: 'CV-M02', turn: 0 },
  { id: 'rel-6', source: 'VS-CVM02', relation: 'monitors', target: 'CV-M02', turn: 0 },
  { id: 'rel-7', source: 'CV-01', relation: 'located_in', target: 'ROOM-PACK-01', turn: 0 },
  { id: 'rel-8', source: 'TS-CVM02-BRG', relation: 'CONTRADICTS', target: 'infrared_pyrometer', status: 'SENSOR_VALIDATION_REQUIRED', turn: 8 }
];

class FactoryMindDataService {
  private currentTurnIndex: number = 2; // Default turn 5 state
  private listeners: Array<() => void> = [];
  private isAutoPlaying: boolean = false;
  private playbackSpeedMs: number = 2000;
  private playbackTimer: any = null;

  public getTurnCount(): number {
    return CANONICAL_TURNS.length;
  }

  public getCurrentTurnIndex(): number {
    return this.currentTurnIndex;
  }

  public getCurrentState(): ScenarioTurnState {
    return CANONICAL_TURNS[this.currentTurnIndex] || CANONICAL_TURNS[CANONICAL_TURNS.length - 1];
  }

  public setTurnIndex(index: number) {
    if (index >= 0 && index < CANONICAL_TURNS.length) {
      this.currentTurnIndex = index;
      this.notify();
    }
  }

  public stepForward() {
    if (this.currentTurnIndex < CANONICAL_TURNS.length - 1) {
      this.currentTurnIndex++;
      this.notify();
    } else {
      this.pause();
    }
  }

  public stepBackward() {
    if (this.currentTurnIndex > 0) {
      this.currentTurnIndex--;
      this.notify();
    }
  }

  public play() {
    if (this.isAutoPlaying) return;
    this.isAutoPlaying = true;
    this.notify();

    this.playbackTimer = setInterval(() => {
      if (this.currentTurnIndex < CANONICAL_TURNS.length - 1) {
        this.stepForward();
      } else {
        this.pause();
      }
    }, this.playbackSpeedMs);
  }

  public pause() {
    this.isAutoPlaying = false;
    if (this.playbackTimer) {
      clearInterval(this.playbackTimer);
      this.playbackTimer = null;
    }
    this.notify();
  }

  public isPlaying(): boolean {
    return this.isAutoPlaying;
  }

  public setPlaybackSpeed(speedMs: number) {
    this.playbackSpeedMs = speedMs;
    if (this.isAutoPlaying) {
      this.pause();
      this.play();
    }
  }

  public subscribe(listener: () => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach(listener => listener());
  }

  public processQuery(queryText: string): ChatMessage {
    const qLower = queryText.toLowerCase().trim();
    const currState = this.getCurrentState();
    const timestamp = new Date().toLocaleTimeString();

    if (qLower.includes('where')) {
      let targetId = 'CV-M02';
      if (qLower.includes('m01')) targetId = 'CV-M01';
      if (qLower.includes('guard')) targetId = 'GUARD-CV01';
      if (qLower.includes('plc') || qLower.includes('pcs')) targetId = 'PCS-CV01';

      const asset = currState.assets[targetId];
      const room = INITIAL_ROOMS[asset?.room || 'ROOM-PACK-01'];

      return {
        id: `msg-${Date.now()}`,
        sender: 'FACTORYMIND_AI',
        text: `[Location Lookup] ${asset?.name || targetId} (${targetId}) is located inside ${room.name} (${room.id}). Confidence score: ${(asset?.confidence || 0.99) * 100}%. Source: Persistent WorldModel Asset Registry.`,
        timestamp,
        query_type: 'LOCATION',
        source: 'world_model_asset_registry',
        target_id: targetId,
        target_room: room.id,
        facts_json: { asset_id: targetId, room: room.id, room_name: room.name }
      };
    }

    if (qLower.includes('abnormal') || qLower.includes('health') || qLower.includes('status')) {
      const asset = currState.assets['CV-M02'];
      const ts = currState.sensors['TS-CVM02-BRG'];
      const vs = currState.sensors['VS-CVM02'];

      return {
        id: `msg-${Date.now()}`,
        sender: 'FACTORYMIND_AI',
        text: `[Abnormality Assessment] YES, CV-M02 (Tail Drive Motor) is currently ABNORMAL (${asset.health_state}). Observed telemetry breaches: Temperature Sensor TS-CVM02-BRG reading is ${ts.latest_value} °C (${ts.status}), Vibration Sensor VS-CVM02 reading is ${vs.latest_value} mm/s (${vs.status}).`,
        timestamp,
        query_type: 'ABNORMALITY',
        source: 'world_model_telemetry',
        target_id: 'CV-M02',
        target_room: 'ROOM-PACK-01',
        facts_json: {
          asset_id: 'CV-M02',
          health_state: asset.health_state,
          temperature: ts.latest_value,
          vibration: vs.latest_value
        }
      };
    }

    if (qLower.includes('safe') || qLower.includes('hazard') || qLower.includes('danger')) {
      const guardState = currState.assets['GUARD-CV01']?.access_state || 'CLOSED';
      const cv01Op = currState.assets['CV-01']?.operational_state || 'RUNNING';

      const isSafe = cv01Op === 'STOPPED' || guardState === 'CLOSED';

      return {
        id: `msg-${Date.now()}`,
        sender: 'FACTORYMIND_AI',
        text: isSafe
          ? `[Safety Status] Packaging Bay 1 (ROOM-PACK-01) is currently SAFE. Machinery status: ${cv01Op}. Interlocked safety guard status: ${guardState}.`
          : `[Safety Status Alert] Packaging Bay 1 (ROOM-PACK-01) has ACTIVE HAZARDS. Running machinery present with elevated bearing thermal & vibration alarms! Guard state: ${guardState}.`,
        timestamp,
        query_type: 'SAFETY',
        source: 'safety_validator_engine',
        target_room: 'ROOM-PACK-01',
        facts_json: { room: 'ROOM-PACK-01', is_safe: isSafe, cv01_op: cv01Op, guard_state: guardState }
      };
    }

    // Default response
    return {
      id: `msg-${Date.now()}`,
      sender: 'FACTORYMIND_AI',
      text: `[WorldModel Query] Analyzed prompt against 5 room nodes and 12 tracked assets. All telemetry trends are reconciled into persistent state. CV-M02 status is ${currState.assets['CV-M02']?.health_state || 'WARNING'}.`,
      timestamp,
      query_type: 'GENERAL',
      source: 'factorymind_query_router',
      target_id: 'CV-M02',
      target_room: 'ROOM-PACK-01'
    };
  }
}

export const factorymindData = new FactoryMindDataService();

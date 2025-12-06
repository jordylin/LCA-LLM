flowchart LR
  %% ====== Observation ======
  subgraph O[Observation (what the agent currently sees)]
    UReq[User request<br/>e.g. "Extract energy inputs"]
    Doc[Document snippet<br/>(from search_document)]
    LCI[LCI DB result<br/>(from search_lci_database)]
    Sum[Session summary<br/>(from get_session_summary)]
  end

  %% ====== Memory ======
  subgraph M[Memory (session actions & flows)]
    DB[(MongoDB<br/>session action log)]
  end

  %% ====== Thought ======
  subgraph T[Thought (reasoning & plan)]
    Think["<think> ... I have recorded materials ...<br/>I still need energy inputs ..."]
    Plan[Plan of next steps<br/>1. Find energy table<br/>2. Record electricity flow]
  end

  %% ====== Action ======
  subgraph A[Action (tool calls)]
    SDoc[Search document<br/>(S-doc)]
    SLci[Search LCI DB<br/>(S-lci)]
    Rec[Record LCI flow<br/>(R-flow)]
  end

  %% ---- Sources to Observation ----
  UReq --> O
  SDoc --> Doc
  SLci --> LCI
  DB -->|get_session_summary| Sum

  %% ---- Observation to Thought ----
  O --> Think
  DB -. historical context .- Think
  Think --> Plan

  %% ---- Thought to Action ----
  Plan --> SDoc
  Plan --> SLci
  Plan --> Rec

  %% ---- Action updates ----
  Rec -->|record_* tools| DB
  SDoc --> O
  SLci --> O

  %% ---- Loop indication ----
  classDef faded fill:#ffffff,stroke-dasharray: 5 5,color:#888;
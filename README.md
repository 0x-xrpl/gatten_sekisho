# GATTEN SEKISHO
## A Digital Checkpoint for Final AI Decisions
### AI実行前の最終デジタル関所

---

## 1. What it is

**GATTEN SEKISHO** は、AIエージェントが“実行”に移る直前に必ず通過する **実行許可の関所** です。  
判断の内容・根拠・リスク・制約適合を審査し、合格したものにのみ **Permit（通行手形 / 実行許可証）** を発行します。

---

## 2. Why now

AIは「提案」までは賢い。  
しかし社会が本当に怖いのは **“実行”** です。

- 誤操作 → 資産移動 / API破壊 / 情報漏えい
- “後からログを見る”では遅い（取り返せない）
- Web3 は 1回の判断がトランザクションになり、不可逆

つまり不足しているのは、**実行の直前に止める仕組み**。

AIに必要なのは「賢さ」ではなく「止まれる構造」。  
**GATTEN SEKISHO** は、AIの実行を“許す／止める”ための標準機構を提供する。

---

## 2.1 Who suffers most

最も困っているのは、AIに「実行権限」を渡す責任を負う人です。  
具体的には、**情シス責任者 / プロダクトオーナー / 運用責任者 / セキュリティ担当 / Web3運用者（鍵管理者）** です。

この人たちは以下を背負います：

- APIキー・管理権限・本番インフラ
- データ（PII含む）・ログ・外部連携先
- ウォレット署名・資産移動・不可逆トランザクション
- 事故時の説明責任（なぜ止めなかったか）

GATTEN SEKISHO は「AIが暴走しない」ではなく、  
「責任者が“止められる制度”を持てる」ことを目的に設計されている。

---

## 3. Core concept

GATTEN SEKISHO は AIの最終判断を **通行審査** に変換します。

- 思考・提案：自由
- 実行：関所の許可が必要（Permitが無いと実行不可）

この分離により、AIは暴走できません。  
実行は常に“許可済みの判断”だけになります。

---

## 4. Requirements

本プロジェクトは、SpoonOSを介したLLM呼び出しおよび、  
Spoon公式ToolまたはMCPに準拠した実行フローを実装済みである。

### 4.1 SpoonOSでLLMを呼ぶ

Execution Flow（固定）:  
Agent → SpoonOS（Unified Protocol Layer） → LLM（via spoon_ai.llm）

必須のフローを明示します：

> **Agent → SpoonOS → LLM**

- Agent: Decision Agent（判断生成）
- SpoonOS: Orchestrator（実行フロー統制）
- LLM: ローカルLLM（Ollama / tinyllama）

### 4.2 Spoon official tool 利用

本プロジェクトは SpoonOS の公式 Tool 体系（BaseTool）を採用し、  
以下を Tool として実装します：

- Policy Tool（規則・制約チェック）
- Storage Tool（ログ保存）
- Crypto/Neo Tool（Permit記録）
- Audit Logger（監査ログ記録）
- Notify Tool（Slack/Email通知）

本実装では Spoon公式 Storage Tool を使用し、  
生成結果および監査ログを永続化する。

### 4.3 エラーハンドリング

- Tool呼び出し失敗時のフォールバック
- LLM出力不正時の再試行
- Neo書き込み失敗時の安全停止

LLMまたはTool呼び出し失敗時は、再試行または安全な  
fallbackレスポンスを返す設計とする。

---

## 5. System: 三関所モデル（Three-Checkpoint Model）

GATTEN SEKISHO は **3つの関所** を順番に通します。  
どこかで落ちたら **必ず止まり**、理由を返す（Fail-Closed）。

---

## 5.1 第一関所：Explain Check（説明審査）

**狙い：その判断は“説明できるか”。**  
説明できない判断は、危険であり実行に値しない。

### 入力

- `user_request`（ユーザー要求）
- `context`（ツール結果 / 参照資料 / 制約）
- `draft_decision`（LLM判断）

### 出力（必須JSON）

```json
{
  "decision": "string",
  "rationale": ["string", "string"],
  "assumptions": ["string"],
  "risks": [
    {
      "risk": "string",
      "severity": "LOW|MEDIUM|HIGH",
      "mitigation": "string"
    }
  ],
  "alternatives": [
    {
      "option": "string",
      "why_not": "string"
    }
  ]
}
```

### 判定ルール

- JSONが壊れている → 再生成（最大3回）→ 失敗なら拒否  
- rationale が空 / risks が無い → 拒否（理由つき）  
- severity が HIGH で mitigation が無い → 拒否  

---

## 5.2 第二関所：Policy Check（規則・制約審査）

**狙い：安全・規約・運用ルールに違反してないか。**

### Policyの例（最低限）

- PII送信禁止（個人情報を外部へ）
- 高額資産移動は人間承認必須
- 未登録ツールは呼べない
- 破壊的操作（delete/drop）は原則禁止

### Policy Tool（SpoonOS BaseTool）インターフェース

```json
{
  "decision": "...",
  "context": {}
}
```

### 戻り値（実装一致）

```json
{
  "ok": true,
  "violations": [],
  "risk_level": "LOW|MEDIUM|HIGH",
  "required_human_approval": false
}
```

### 判定ルール

- violations 1つでもあれば拒否  
- required_human_approval=true なら「保留」（実行禁止だが提案は返す）  

---

## 5.2.1 Policy as Code

Policyは「例」ではなく「制度」として運用される。

- Policy Versioning：policy_version を Permit に刻む  
- Statusの標準化：APPROVED / DENIED / HOLD を正式ステータス化  
- Policy定義の外部化：Policyはコードではなく policy.yaml / policy.json として管理される  
- 変更管理：Policy更新はレビュー対象（監査上の要件）  

---

## 5.3 第三関所：Permit Issue（通行手形 / 実行許可証）

**狙い：審査を通った“事実”を改ざん不能にする。**  
Permit が無い判断は 実行できない。

### Permit（通行手形）フォーマット

```json
{
  "permit_id": "uuid",
  "decision_hash": "sha256(explain_json)",
  "policy_version": "v1.0",
  "risk_level": "LOW|MEDIUM|HIGH",
  "issued_at": "timestamp",
  "expires_at": "timestamp",
  "neo_mode": "string",
  "neo_tx_hash": "0x..."
}
```

---

## 6. Why Neo

Neoを使う理由は“Web3だから”ではない。  
GATTEN SEKISHO の本質は **「許可の証明」** です。

必要なのは：

- 改ざん不能（後で書き換え不可）
- 第三者検証可能（監査・審査員・企業が見れる）
- 分散環境で共通参照できる

Neo は Permit を **“公的な許可証”** として置く台帳になる。

Permit をチェーンに刻む＝「裁可の痕跡」が消えない。  
AIの実行が “証明可能な許可” に変わる。

---

## 7. Architecture

```text
[UI/Client]
   |
   v
[API Gateway (FastAPI)]
   |
   v
[SpoonOS Orchestrator]
   |
   +--> (1) Decision Agent   ---SpoonOS--> Ollama (tinyllama)
   |
   +--> (2) Explain Check    ---validate JSON schema
   |
   +--> (3) Policy Tool      ---rules / constraints / risk
   |
   +--> (4) Permit Issuer    ---hash + permit object
   |
   +--> (5) Neo Writer Tool  ---write permit hash -> tx
   |
   +--> (6) Execution Guard  ---block unless permit valid
   |
   +--> (7) Audit Logger     ---append audit events
   |
   +--> (8) Storage Tool     ---local JSONL logs
   |
   +--> (9) Notify Tool      ---Slack/Email
```

---

## 8. Repo Structure

```text
gatten-gate/
  README.md
  apps/
    api/                 # FastAPI entry
      main.py
      routes.py
  spoon/
    orchestrator.py      # custom Orchestrator
    agents/
      decision_agent.py
      explain_agent.py
    tools/               # SpoonOS BaseTool implementations
      policy_tool.py
      neo_tool.py
      storage_tool.py
      notify_tool.py
  contracts/
    permit_registry.py   # neo3-boa smart contract
  schemas/
    explain.schema.json
    permit.schema.json
  scripts/
    demo_scenario.sh
    neo/
      local_chain_start.sh
      deploy_contract.sh
      smoke_test.sh
  tests/
    test_explain.py
    test_policy.py
    test_permit.py
    test_execute.py
    test_fail_closed.py
```

---

## 9. Execution Guard（Permit無し実行を物理的に封鎖）

GATTEN SEKISHO の勝ち筋はここ。  
“ログを残す”じゃ弱い。止める仕組みが必要。

### 実装要件

- 実行は /gate/execute の単一ゲートでのみ許可される
- Permitが無い・期限切れ・ハッシュ不一致 → 実行拒否
- Permitが有効 → 実行許可

---

## 9.1 Invariants（不変条件）

以下は仕様上の“不変条件（Invariant）”であり、例外は存在しない：

- すべての実行は /gate/execute を必ず経由し、Permit検証はここで一括実行される
- Permitが無い / 期限切れ / ハッシュ不一致の場合、処理は必ず失敗（Fail-Closed）
- 実行の許可判定は Execution Guard（/gate/execute）に中央集約され、各Tool実装で回避できない
- Permit検証は「決定内容（Explain JSON）」のハッシュ一致で行い、別決定の流用を許さない

### 推奨テスト（最低限）

- test_exec_denied_without_permit
- test_exec_denied_hash_mismatch
- test_exec_denied_expired_permit
- test_exec_allowed_with_valid_permit

---

## 9.2 API: /gate/execute（実装完全一致）

/gate/execute は Permit を持つ実行だけを通す「実行ゲート」です。  
実装は以下の入力形式に一致します。

### Request

```json
{
  "permit_id": "uuid",
  "action": {
    "tool": "string",
    "payload": {}
  }
}
```

### Server-side checks（Fail-Closed）

- Permit が存在すること
- Permit が期限内であること
- decision_hash が一致すること

※ /gate/execute は Policy の APPROVED チェックを行いません。  
（Permit の存在・期限・hash一致のみで実行可否を決定します）

### Response（実装一致）

```json
{
  "ok": true,
  "status": "EXECUTED|REJECTED|ERROR",
  "reason": "string",
  "neo_tx_hash": "0x...",
  "neo_mode": "string"
}
```

---

## 10. Smart Contract Spec（Neo Permit Registry）

### 保存する最小データ

- permit_id
- decision_hash
- issued_at
- expires_at
- policy_version

### Contract API（実装一致）

- register_permit(permit_id, decision_hash, issued_at, expires_at, policy_version)
- get_permit(permit_id) -> struct
- is_valid(permit_id, decision_hash, now) -> bool

※ neo_mode はコントラクトには渡しません。  
（アプリケーション層の情報として Permit に保持されます）

---

## 11. Data & Audit（監査＝奉行所の“台帳”）

チェーンは「公文書」。  
アプリは「台帳」。

### 保存するログ（現行：AuditLogger + StorageTool による local JSONL）

- request_id / permit_id
- user_request
- explain_json
- policy_result
- neo_tx_hash
- final_status (APPROVED / DENIED / HOLD)
- timestamps

---

## 11.1 Accountability

GATTEN SEKISHO は「AIが説明できる」ではなく、  
「責任者が説明できる形式」を生成する。

- Explain JSON は人間向けの説明文ではなく、監査・再現・検証可能な形式
- Permitは「誰が、どの規則で、何を許可したか」を示す最小証明
- HOLDは「実行していない」ことを制度として示せる（責任回避ではなく責任遂行）

これにより、AI運用は“属人的な判断”ではなく“制度的な裁可”になる。

---

## License

```text
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

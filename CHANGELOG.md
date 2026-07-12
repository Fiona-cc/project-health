# Changelog

## 0.3.0（2026-07-12）

### Added
- **Phase 2**: watch structured comparison（`watch/scripts/compare.py`）——按 finding.id 确定性 diff
- **Phase 3**: fix safety hardening（execution.trust / 精确回滚 / 基线失败处理）
- **Phase 4**: blueprint + spec 文档同步（self-dogfooding）
- **Phase 5**: Constitution v2（severity 与 enforcement.kind 拆分）
- **Phase 6**: A/B bridge——C5 constitution check in scan.py（可执行规则自动查）

### Changed
- setup config schema 与正式契约统一
- fix suppression ID 改为从 audit 取原 id（修复"写了不生效"bug）
- DL 领域包修正三处事实性错误（validation/test 区分、数据存储、种子可复现性）
- README 全面同步（五 skill、scripts/依赖、目录树）

## 0.2.0（2026-07-10）

### Added
- **B 面**: design skill（设计顾问）+ 前端精装领域包 + DL 薄包
- **A 面加固**: scan.py 确定性扫描引擎 + golden 金测体系
- finding 数据契约（schema-contract v1）

## 0.1.0（2026-07-10）

### Added
- **A 面**: audit / fix / setup / watch 四个 Claude Code Skill
- blueprint 完整蓝图
- GitHub 发布

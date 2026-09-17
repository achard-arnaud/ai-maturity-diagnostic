# Epic 13 S04 stop condition

Every experiment links a LearningProposal to immutable baseline and canary
references, a primary metric, minimum sample, tolerated regression and NRT
drift threshold. Canary promotion is impossible below sample size; regression
or drift produces an explicit rollback decision.

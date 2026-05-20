# Test-Protokoll

- Datum: 2026-05-20 14:30:28 UTC
- Host: Toto241 (Windows-10-10.0.26200-SP0)
- Python: 3.11.9
- Target: `tests`
- Laufzeit pytest: 141.98 s

**Entscheidung:** GO

## Gesamtuebersicht

| Status | Anzahl |
| --- | ---: |
| passed | 478 |
| failed | 0 |
| error | 0 |
| skipped | 3 |
| **gesamt** | **481** |
| Dauer (Summe) | 140.16 s |

## Abdeckung nach Konzept-Bereich (Anhang)

| Bereich (Anhang) | Tests | passed | failed | error | skipped | Dauer (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kapitel 2 / Anhang D - Mitglieder-Szenarien | 18 | 18 | 0 | 0 | 0 | 67.38 |
| Anhang D - Rollen- und Berechtigungsmatrix | 69 | 69 | 0 | 0 | 0 | 0.91 |
| Kapitel 3 / Anhang C - Pairwise-Matrix | 13 | 13 | 0 | 0 | 0 | 4.53 |
| Kapitel 8 - Property-/Fuzz-Tests | 29 | 29 | 0 | 0 | 0 | 9.69 |
| Kapitel 4.5 / Anhang J - Release-Gate | 10 | 10 | 0 | 0 | 0 | 1.05 |

## Ergebnisse pro Testdatei

| Datei | Tests | passed | failed | error | skipped | Dauer (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TestAssistantLogRotation | 1 | 1 | 0 | 0 | 0 | 0.33 |
| TestAutoBackup | 2 | 2 | 0 | 0 | 0 | 0.52 |
| TestBackupAndRestore | 3 | 3 | 0 | 0 | 0 | 2.40 |
| TestBackupSqlCipherPath | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestBulkInsertPerformance | 3 | 3 | 0 | 0 | 0 | 6.66 |
| TestBulkOperations | 3 | 3 | 0 | 0 | 0 | 0.73 |
| TestCalendarNoMutation | 1 | 1 | 0 | 0 | 0 | 0.18 |
| TestCheckDemoData | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestCheckPermissions | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestCheckSdkLevels | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestCheckSecrets | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestCheckVersioning | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestCodeSmells | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestCompleteTaskCatchUp | 1 | 1 | 0 | 0 | 0 | 0.46 |
| TestConversationHistory | 1 | 1 | 0 | 0 | 0 | 0.21 |
| TestCsvExport | 2 | 2 | 0 | 0 | 0 | 1.05 |
| TestCsvImportRoundTrip | 3 | 3 | 0 | 0 | 0 | 0.93 |
| TestDashboardSummary | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestDayStructurePersistence | 1 | 1 | 0 | 0 | 0 | 0.21 |
| TestDaysUntil | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestDeadlineCalculationPerformance | 1 | 1 | 0 | 0 | 0 | 0.13 |
| TestDefaultSecureStore | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestDeleteCapabilities | 4 | 4 | 0 | 0 | 0 | 1.53 |
| TestDestructiveFlags | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestDiagnose | 1 | 1 | 0 | 0 | 0 | 1.07 |
| TestDisabledModuleSurfaced | 1 | 1 | 0 | 0 | 0 | 0.75 |
| TestEncryption | 2 | 2 | 0 | 0 | 0 | 0.14 |
| TestFingerprint | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestFormatCurrency | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestGeminiAssistantStub | 2 | 2 | 0 | 0 | 0 | 0.39 |
| TestGeminiRealApi | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestGroupByModule | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestGuiImports | 5 | 5 | 0 | 0 | 0 | 0.10 |
| TestHasCapabilityHonorsDisabled | 2 | 2 | 0 | 0 | 0 | 0.39 |
| TestHkdf | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestHttpSyncRoundTrip | 1 | 1 | 0 | 0 | 0 | 0.53 |
| TestHttpsSyncServer | 1 | 1 | 0 | 0 | 0 | 0.77 |
| TestI18n | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestIcalExport | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestIcalImportRoundTrip | 2 | 2 | 0 | 0 | 0 | 0.66 |
| TestIdentity | 7 | 7 | 0 | 0 | 0 | 0.01 |
| TestImapAbruf | 1 | 1 | 0 | 0 | 0 | 0.20 |
| TestInMemorySecureStore | 8 | 8 | 0 | 0 | 0 | 0.01 |
| TestInboxExtractText | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestInputValidation | 6 | 6 | 0 | 0 | 0 | 3.43 |
| TestKeyringSecureStore | 4 | 4 | 0 | 0 | 0 | 0.10 |
| TestLamportCrdt | 3 | 3 | 0 | 0 | 0 | 0.20 |
| TestLicensing | 78 | 78 | 0 | 0 | 0 | 5.89 |
| TestLlmJsonParsing | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestLlmProposalValidation | 2 | 2 | 0 | 0 | 0 | 1.79 |
| TestMainImports | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestModuleStatePersistence | 1 | 1 | 0 | 0 | 0 | 0.22 |
| TestNotesListingPerformance | 1 | 1 | 0 | 0 | 0 | 5.53 |
| TestNotesModule | 4 | 4 | 0 | 0 | 0 | 0.78 |
| TestOcrParsing | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestPairingFailures | 5 | 5 | 0 | 0 | 0 | 0.09 |
| TestPairingHappyPath | 3 | 3 | 0 | 0 | 0 | 0.09 |
| TestParseBuildozerSpec | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestPrintFileNoShell | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestPrinten | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestProfile | 7 | 7 | 0 | 0 | 0 | 0.38 |
| TestPropertyBasedSkipped | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestProposalUpdate | 3 | 3 | 0 | 0 | 0 | 0.58 |
| TestProposalsFlow | 1 | 1 | 0 | 0 | 0 | 0.23 |
| TestRecurrenceValidation | 5 | 5 | 0 | 0 | 0 | 0.89 |
| TestRegistry | 3 | 3 | 0 | 0 | 0 | 0.52 |
| TestRegistryGetCapability | 3 | 3 | 0 | 0 | 0 | 0.51 |
| TestRelativeWhen | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestReportFormats | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestReviewFixes | 18 | 18 | 0 | 0 | 0 | 7.54 |
| TestRunChecksIntegration | 2 | 2 | 0 | 0 | 0 | 0.12 |
| TestSearch | 3 | 3 | 0 | 0 | 0 | 1.31 |
| TestSecretsDoNotLeak | 1 | 1 | 0 | 0 | 0 | 0.02 |
| TestSettings | 4 | 4 | 0 | 0 | 0 | 0.71 |
| TestSmtpVersand | 4 | 4 | 0 | 0 | 0 | 0.01 |
| TestSmtpWiring | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestSqlCipherRealRoundTrip | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestSqlCipherValidation | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestStatistics | 5 | 5 | 0 | 0 | 0 | 1.12 |
| TestSyncCompaction | 1 | 1 | 0 | 0 | 0 | 0.03 |
| TestSyncExpandedCapabilities | 1 | 1 | 0 | 0 | 0 | 0.41 |
| TestSyncReentry | 2 | 2 | 0 | 0 | 0 | 0.44 |
| TestSyncServerCompaction | 1 | 1 | 0 | 0 | 0 | 0.58 |
| TestSyncServerTls | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestThreadSafety | 1 | 1 | 0 | 0 | 0 | 0.64 |
| TestTranscript | 7 | 7 | 0 | 0 | 0 | 0.01 |
| TestTruncate | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestUrgencyColor | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestUtcTimestamps | 1 | 1 | 0 | 0 | 0 | 0.39 |
| TestUtcTimestampsInDb | 2 | 2 | 0 | 0 | 0 | 0.42 |
| TestVCardExport | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestVCardImportRoundTrip | 1 | 1 | 0 | 0 | 0 | 0.36 |
| TestYearlyPdfReport | 1 | 1 | 0 | 0 | 0 | 0.20 |
| test_members_scenarios | 18 | 18 | 0 | 0 | 0 | 67.38 |
| test_pairwise_matrix | 13 | 13 | 0 | 0 | 0 | 4.53 |
| test_properties_concept | 29 | 29 | 0 | 0 | 0 | 9.69 |
| test_protocol_generator | 4 | 4 | 0 | 0 | 0 | 0.05 |
| test_release_gate | 10 | 10 | 0 | 0 | 0 | 1.05 |
| test_roles_permissions | 69 | 69 | 0 | 0 | 0 | 0.91 |

## Vollstaendige Test-Liste

| Status | Test-ID | Dauer (s) |
| --- | --- | ---: |
| [pass] | `tests.concept.test_members_scenarios::test_M01_single_owner_no_rotation` | 0.387 |
| [pass] | `tests.concept.test_members_scenarios::test_M02_minimal_team_two_members` | 0.760 |
| [pass] | `tests.concept.test_members_scenarios::test_M05_meets_play_minimum_12` | 4.374 |
| [pass] | `tests.concept.test_members_scenarios::test_M06_scales_to_twenty_plus` | 6.218 |
| [pass] | `tests.concept.test_members_scenarios::test_M07_mixed_status_distribution` | 4.543 |
| [pass] | `tests.concept.test_members_scenarios::test_M08_invited_only_owner_active` | 0.618 |
| [pass] | `tests.concept.test_members_scenarios::test_M09_reactivation_restores_member` | 1.280 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-01]` | 0.507 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-02]` | 0.839 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-03]` | 1.822 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-04]` | 3.368 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-05]` | 4.297 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-06]` | 6.415 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-07]` | 4.596 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-08]` | 0.652 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-09]` | 1.121 |
| [pass] | `tests.concept.test_members_scenarios::test_get_events_handles_all_sizes` | 23.807 |
| [pass] | `tests.concept.test_members_scenarios::test_remove_and_readd_preserves_distinct_id` | 1.773 |
| [pass] | `tests.concept.test_pairwise_matrix::test_artifact_tsv_written` | 0.001 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_covers_at_least_95_percent_of_pairs` | 0.022 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_has_acceptable_size` | 0.001 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_is_deterministic` | 1.689 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_respects_constraints` | 0.867 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[0]` | 0.190 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[100]` | 0.221 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[125]` | 0.227 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[150]` | 0.305 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[175]` | 0.270 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[25]` | 0.200 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[50]` | 0.254 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[75]` | 0.281 |
| [pass] | `tests.concept.test_properties_concept::test_P1_rotation_advances_one_step` | 3.885 |
| [pass] | `tests.concept.test_properties_concept::test_P2_overdue_task_rolls_forward_to_future` | 4.016 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[DATA_EXPORT]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[GROUP_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[GROUP_DELETE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[MEMBER_CHANGE_ROLE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[MEMBER_INVITE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[MEMBER_REMOVE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[OWNERSHIP_TRANSFER]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[TASK_ASSIGN_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[TASK_CLOSE_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P3_guest_cannot_perform_destructive[TASK_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[COMMENT]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[DATA_EXPORT]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[GROUP_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[GROUP_DELETE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[MEMBER_CHANGE_ROLE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[MEMBER_INVITE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[MEMBER_REMOVE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[OWNERSHIP_TRANSFER]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[PUSH_SETTINGS_SELF]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[TASK_ASSIGN_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[TASK_ASSIGN_SELF]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[TASK_CLOSE_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[TASK_CLOSE_OWN]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[TASK_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P4_owner_allowed_everything[TASK_VIEW]` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P5_classify_urgency_is_monotonic` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P6_pairwise_deterministic` | 1.764 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_artifacts_present_after_run` | 0.001 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_classifies_and_decides` | 0.003 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_formats_markdown` | 0.033 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_parses_junit` | 0.011 |
| [pass] | `tests.concept.test_release_gate::test_J10_full_module_registry_assembles` | 0.143 |
| [pass] | `tests.concept.test_release_gate::test_J1_version_code_is_positive_integer` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J2_privacy_documents_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J3_license_file_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J4_playstore_doc_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J5_testing_doc_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J6_concept_modules_import` | 0.000 |
| [pass] | `tests.concept.test_release_gate::test_J7_pairwise_matrix_has_full_coverage` | 0.902 |
| [pass] | `tests.concept.test_release_gate::test_J8_permission_matrix_is_complete` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J9_member_profiles_present` | 0.000 |
| [pass] | `tests.concept.test_roles_permissions::test_admin_can_invite_but_not_delete_group` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__COMMENT]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__DATA_EXPORT]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__GROUP_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__GROUP_DELETE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__MEMBER_CHANGE_ROLE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__MEMBER_INVITE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__MEMBER_REMOVE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__OWNERSHIP_TRANSFER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__PUSH_SETTINGS_SELF]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__TASK_ASSIGN_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__TASK_ASSIGN_SELF]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__TASK_CLOSE_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__TASK_CLOSE_OWN]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__TASK_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[ADMIN__TASK_VIEW]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__COMMENT]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__DATA_EXPORT]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__GROUP_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__GROUP_DELETE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__MEMBER_CHANGE_ROLE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__MEMBER_INVITE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__MEMBER_REMOVE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__OWNERSHIP_TRANSFER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__PUSH_SETTINGS_SELF]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__TASK_ASSIGN_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__TASK_ASSIGN_SELF]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__TASK_CLOSE_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__TASK_CLOSE_OWN]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__TASK_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[GUEST__TASK_VIEW]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__COMMENT]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__DATA_EXPORT]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__GROUP_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__GROUP_DELETE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__MEMBER_CHANGE_ROLE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__MEMBER_INVITE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__MEMBER_REMOVE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__OWNERSHIP_TRANSFER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__PUSH_SETTINGS_SELF]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__TASK_ASSIGN_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__TASK_ASSIGN_SELF]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__TASK_CLOSE_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__TASK_CLOSE_OWN]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__TASK_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[MEMBER__TASK_VIEW]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__COMMENT]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__DATA_EXPORT]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__GROUP_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__GROUP_DELETE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__MEMBER_CHANGE_ROLE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__MEMBER_INVITE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__MEMBER_REMOVE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__OWNERSHIP_TRANSFER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__PUSH_SETTINGS_SELF]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__TASK_ASSIGN_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__TASK_ASSIGN_SELF]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__TASK_CLOSE_OTHER]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__TASK_CLOSE_OWN]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__TASK_CREATE]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_concept_matrix_complete[OWNER__TASK_VIEW]` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_destructive_capabilities_have_marker` | 0.181 |
| [pass] | `tests.concept.test_roles_permissions::test_guest_cannot_modify_data` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_license_gate_blocks_ai_in_free` | 0.157 |
| [pass] | `tests.concept.test_roles_permissions::test_license_gate_blocks_finance_writes_in_free` | 0.170 |
| [pass] | `tests.concept.test_roles_permissions::test_license_gate_passes_family_in_free` | 0.168 |
| [pass] | `tests.concept.test_roles_permissions::test_member_can_self_assign_but_not_other` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_owner_can_do_everything` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_owner_concept_role_maps_to_pro_license` | 0.173 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_geometry_helpers` | 0.082 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_gui_has_license_section_methods` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_gui_module_imports` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_license_ui_helpers_callable_headless` | 0.012 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_main_app_class_exists` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestMainImports::test_build_registry_signature` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestMainImports::test_main_module_imports` | 0.001 |
| [pass] | `tests.test_integration.TestHttpsSyncServer::test_tls_handshake_with_self_signed_cert` | 0.766 |
| [pass] | `tests.test_integration.TestImapAbruf::test_fetch_imap_loops_through_unseen` | 0.195 |
| [pass] | `tests.test_integration.TestOcrParsing::test_missing_engine_returns_hint` | 0.002 |
| [pass] | `tests.test_integration.TestOcrParsing::test_receipt_text_extraction` | 0.001 |
| [pass] | `tests.test_integration.TestPrinten::test_print_file_calls_lpr_on_macos` | 0.005 |
| [pass] | `tests.test_integration.TestPrinten::test_print_file_calls_subprocess_on_unix` | 0.005 |
| [pass] | `tests.test_integration.TestPrinten::test_print_file_missing_returns_error` | 0.002 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_calls_protocol` | 0.008 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_handles_server_error` | 0.002 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_skips_starttls_when_disabled` | 0.003 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_without_config_returns_skip` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDashboardSummary::test_aggregates_three_sources` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDashboardSummary::test_robust_against_errors` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDashboardSummary::test_truncates_to_phone_friendly_count` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDaysUntil::test_future` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDaysUntil::test_invalid` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDaysUntil::test_past` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDaysUntil::test_today` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_invalid` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_normal` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_other_currency` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_thousands_separator` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_zero` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestGroupByModule::test_groups_by_module_id` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestGroupByModule::test_unknown_falls_back` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestRelativeWhen::test_future` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestRelativeWhen::test_invalid_returns_empty` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestRelativeWhen::test_past` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestRelativeWhen::test_today` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestRelativeWhen::test_tomorrow` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestRelativeWhen::test_yesterday` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestTruncate::test_empty` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestTruncate::test_long_gets_ellipsis` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestTruncate::test_short_unchanged` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestUrgencyColor::test_far_future_is_normal` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestUrgencyColor::test_none_is_normal` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestUrgencyColor::test_overdue_is_error` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestUrgencyColor::test_within_month_is_warning` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestUrgencyColor::test_within_week_is_error` | 0.001 |
| [pass] | `tests.test_pairing.TestDefaultSecureStore::test_env_override_to_memory` | 0.001 |
| [pass] | `tests.test_pairing.TestDefaultSecureStore::test_returns_some_secure_store` | 0.001 |
| [pass] | `tests.test_pairing.TestFingerprint::test_fingerprint_bits_constant_matches_format` | 0.001 |
| [pass] | `tests.test_pairing.TestFingerprint::test_fingerprint_differs_for_different_keys` | 0.001 |
| [pass] | `tests.test_pairing.TestFingerprint::test_fingerprint_format` | 0.001 |
| [pass] | `tests.test_pairing.TestFingerprint::test_fingerprint_is_deterministic` | 0.001 |
| [pass] | `tests.test_pairing.TestFingerprint::test_fingerprint_known_vector` | 0.001 |
| [pass] | `tests.test_pairing.TestFingerprint::test_fingerprint_rejects_wrong_length` | 0.001 |
| [pass] | `tests.test_pairing.TestIdentity::test_generate_identity_accepts_custom_name` | 0.001 |
| [pass] | `tests.test_pairing.TestIdentity::test_generate_identity_returns_valid_pair` | 0.001 |
| [pass] | `tests.test_pairing.TestIdentity::test_sign_verify_roundtrip` | 0.001 |
| [pass] | `tests.test_pairing.TestIdentity::test_two_identities_are_distinct` | 0.001 |
| [pass] | `tests.test_pairing.TestIdentity::test_verify_rejects_tampered_message` | 0.001 |
| [pass] | `tests.test_pairing.TestIdentity::test_verify_rejects_wrong_public_key` | 0.001 |
| [pass] | `tests.test_pairing.TestIdentity::test_verify_returns_false_for_garbage_signature` | 0.001 |
| [pass] | `tests.test_pairing.TestInMemorySecureStore::test_delete_makes_key_disappear` | 0.001 |
| [pass] | `tests.test_pairing.TestInMemorySecureStore::test_delete_missing_is_silent` | 0.001 |
| [pass] | `tests.test_pairing.TestInMemorySecureStore::test_get_missing_returns_none` | 0.001 |
| [pass] | `tests.test_pairing.TestInMemorySecureStore::test_list_keys_filters_by_prefix` | 0.001 |
| [pass] | `tests.test_pairing.TestInMemorySecureStore::test_overwrite_replaces_value` | 0.001 |
| [pass] | `tests.test_pairing.TestInMemorySecureStore::test_protocol_runtime_check` | 0.001 |
| [pass] | `tests.test_pairing.TestInMemorySecureStore::test_rejects_non_bytes` | 0.001 |
| [pass] | `tests.test_pairing.TestInMemorySecureStore::test_set_and_get_roundtrip` | 0.001 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_delete_removes_from_list` | 0.028 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_list_keys_returns_set_keys` | 0.045 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_manifest_key_is_reserved` | 0.002 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_roundtrip` | 0.020 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_default_length_32` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_deterministic` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_distinct_inputs_distinct_outputs` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_rejects_bad_length` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_calls_in_wrong_order_raise` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_initiator_cannot_make_proof_before_learning_responder_key` | 0.021 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_rejects_bad_signature_length` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_responder_with_wrong_initiator_pubkey_in_invitation` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_wrong_ot_secret_breaks_handshake` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingHappyPath::test_both_sides_derive_same_psk` | 0.023 |
| [pass] | `tests.test_pairing_handshake.TestPairingHappyPath::test_each_side_learns_the_other_public_key` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingHappyPath::test_psk_symmetric_under_role_swap` | 0.044 |
| [pass] | `tests.test_pairing_handshake.TestSecretsDoNotLeak::test_result_only_exposes_safe_fields` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_deterministic` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_field_swap_does_not_collide` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_method_change_changes_transcript` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_rejects_empty_method_or_sid` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_rejects_negative_or_huge_exp` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_rejects_wrong_pubkey_length` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_transcript_hash_is_32_bytes` | 0.001 |
| [pass] | `tests.test_performance.TestBulkInsertPerformance::test_insert_500_contracts_under_15s` | 2.722 |
| [pass] | `tests.test_performance.TestBulkInsertPerformance::test_insert_500_expenses_under_15s` | 2.789 |
| [pass] | `tests.test_performance.TestBulkInsertPerformance::test_list_200_contracts_under_2s` | 1.149 |
| [pass] | `tests.test_performance.TestDeadlineCalculationPerformance::test_deadline_calculation_scales` | 0.126 |
| [pass] | `tests.test_performance.TestNotesListingPerformance::test_list_attached_in_large_dataset` | 5.533 |
| [pass] | `tests.test_playstore_check.TestCheckDemoData::test_fails_when_db_missing` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckDemoData::test_passes_when_db_and_sqlite_excluded` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckPermissions::test_denied_permission_fails` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckPermissions::test_empty_permissions_passes` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckPermissions::test_unknown_permission_warns` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckPermissions::test_whitelisted_passes` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckSdkLevels::test_fails_below_min_target` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckSdkLevels::test_flags_too_low_minapi` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckSdkLevels::test_passes_at_or_above_target` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckSecrets::test_clean_repo_passes` | 0.007 |
| [pass] | `tests.test_playstore_check.TestCheckSecrets::test_detects_google_api_key` | 0.005 |
| [pass] | `tests.test_playstore_check.TestCheckVersioning::test_invalid_warns` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckVersioning::test_missing_fails` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckVersioning::test_semver_passes` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCodeSmells::test_print_only_in_mobile_path` | 0.005 |
| [pass] | `tests.test_playstore_check.TestCodeSmells::test_requests_verify_false_is_smell` | 0.006 |
| [pass] | `tests.test_playstore_check.TestParseBuildozerSpec::test_extracts_app_block` | 0.002 |
| [pass] | `tests.test_playstore_check.TestParseBuildozerSpec::test_handles_missing_file` | 0.001 |
| [pass] | `tests.test_playstore_check.TestParseBuildozerSpec::test_ignores_comments_and_blanks` | 0.002 |
| [pass] | `tests.test_playstore_check.TestReportFormats::test_json_format_valid` | 0.001 |
| [pass] | `tests.test_playstore_check.TestReportFormats::test_summary_counts` | 0.001 |
| [pass] | `tests.test_playstore_check.TestRunChecksIntegration::test_runs_without_exception` | 0.113 |
| [pass] | `tests.test_playstore_check.TestRunChecksIntegration::test_subset_only` | 0.004 |
| [pass] | `tests.test_smoke.TestAssistantLogRotation::test_log_does_not_grow_unbounded` | 0.326 |
| [pass] | `tests.test_smoke.TestAutoBackup::test_prune_old_backups_keeps_newest` | 0.231 |
| [pass] | `tests.test_smoke.TestAutoBackup::test_run_once_creates_backup_and_prunes` | 0.288 |
| [pass] | `tests.test_smoke.TestBackupAndRestore::test_list_backups_sorted_newest_first` | 1.002 |
| [pass] | `tests.test_smoke.TestBackupAndRestore::test_online_backup_creates_readable_copy` | 0.562 |
| [pass] | `tests.test_smoke.TestBackupAndRestore::test_restore_overwrites_live_db` | 0.838 |
| [pass] | `tests.test_smoke.TestBackupSqlCipherPath::test_sqlcipher_path_rejects_short_key` | 0.002 |
| [pass] | `tests.test_smoke.TestBackupSqlCipherPath::test_sqlcipher_path_requires_key` | 0.002 |
| [pass] | `tests.test_smoke.TestBulkOperations::test_bulk_complete_overdue_tasks` | 0.255 |
| [pass] | `tests.test_smoke.TestBulkOperations::test_bulk_delete_archived` | 0.232 |
| [pass] | `tests.test_smoke.TestBulkOperations::test_bulk_reject_open_proposals` | 0.248 |
| [pass] | `tests.test_smoke.TestCalendarNoMutation::test_recurring_event_not_mutated_in_db` | 0.178 |
| [pass] | `tests.test_smoke.TestCompleteTaskCatchUp::test_overdue_task_advances_rotation_multiple_times` | 0.463 |
| [pass] | `tests.test_smoke.TestConversationHistory::test_history_grows_across_calls` | 0.206 |
| [pass] | `tests.test_smoke.TestCsvExport::test_export_all_writes_five_files` | 0.722 |
| [pass] | `tests.test_smoke.TestCsvExport::test_export_contracts_writes_csv` | 0.328 |
| [pass] | `tests.test_smoke.TestCsvImportRoundTrip::test_export_then_import_reproduces_data` | 0.476 |
| [pass] | `tests.test_smoke.TestCsvImportRoundTrip::test_invalid_dates_dont_crash` | 0.214 |
| [pass] | `tests.test_smoke.TestCsvImportRoundTrip::test_missing_csv_files_are_skipped` | 0.241 |
| [pass] | `tests.test_smoke.TestDayStructurePersistence::test_entry_persists` | 0.209 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_caps_are_destructive` | 0.474 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_contract_round_trip` | 0.404 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_member_keeps_orphan_contracts` | 0.353 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_unknown_returns_error` | 0.298 |
| [pass] | `tests.test_smoke.TestDestructiveFlags::test_critical_capabilities_are_marked` | 0.194 |
| [pass] | `tests.test_smoke.TestDiagnose::test_collect_returns_expected_shape` | 1.066 |
| [pass] | `tests.test_smoke.TestDisabledModuleSurfaced::test_disabled_contracts_yields_warning_in_finance_events` | 0.752 |
| [pass] | `tests.test_smoke.TestEncryption::test_encryption_requires_sqlcipher3` | 0.003 |
| [pass] | `tests.test_smoke.TestEncryption::test_plain_mode_when_no_key` | 0.137 |
| [pass] | `tests.test_smoke.TestGeminiAssistantStub::test_mode_reports_llm` | 0.207 |
| [pass] | `tests.test_smoke.TestGeminiAssistantStub::test_token_usage_accumulates` | 0.184 |
| [pass] | `tests.test_smoke.TestHasCapabilityHonorsDisabled::test_has_capability_false_when_disabled` | 0.190 |
| [pass] | `tests.test_smoke.TestHasCapabilityHonorsDisabled::test_has_capability_returns_after_enable` | 0.195 |
| [pass] | `tests.test_smoke.TestHttpSyncRoundTrip::test_http_provider_append_and_fetch` | 0.528 |
| [pass] | `tests.test_smoke.TestI18n::test_default_german` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_en_missing_key_falls_back_to_de` | 0.002 |
| [pass] | `tests.test_smoke.TestI18n::test_english_translation` | 0.002 |
| [pass] | `tests.test_smoke.TestI18n::test_missing_key_returns_key` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_missing_key_with_default` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_unknown_language_falls_back_to_default` | 0.001 |
| [pass] | `tests.test_smoke.TestIcalExport::test_export_creates_valid_ical` | 0.194 |
| [pass] | `tests.test_smoke.TestIcalImportRoundTrip::test_import_missing_file_returns_error` | 0.178 |
| [pass] | `tests.test_smoke.TestIcalImportRoundTrip::test_roundtrip` | 0.478 |
| [pass] | `tests.test_smoke.TestInboxExtractText::test_empty_payload_returns_empty_string` | 0.001 |
| [pass] | `tests.test_smoke.TestInboxExtractText::test_multipart_without_textplain_returns_empty` | 0.001 |
| [pass] | `tests.test_smoke.TestInputValidation::test_calendar_unknown_category_normalizes` | 0.356 |
| [pass] | `tests.test_smoke.TestInputValidation::test_family_task_rejects_zero_interval` | 0.590 |
| [pass] | `tests.test_smoke.TestInputValidation::test_finance_rejects_bad_date` | 0.584 |
| [pass] | `tests.test_smoke.TestInputValidation::test_finance_rejects_negative_amount` | 0.740 |
| [pass] | `tests.test_smoke.TestInputValidation::test_social_rejects_empty_name` | 0.403 |
| [pass] | `tests.test_smoke.TestInputValidation::test_social_rejects_non_positive_cadence` | 0.762 |
| [pass] | `tests.test_smoke.TestLamportCrdt::test_clock_ticks_monotonically` | 0.001 |
| [pass] | `tests.test_smoke.TestLamportCrdt::test_events_get_lamport_counter` | 0.192 |
| [pass] | `tests.test_smoke.TestLamportCrdt::test_replay_order_uses_lamport` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_apply_token_rejects_empty` | 0.195 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_apply_token_rejects_garbage` | 0.147 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_apply_token_round_trip` | 0.202 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_start_trial_success_then_blocked` | 0.179 |
| [pass] | `tests.test_smoke.TestLicensing::test_activate_pro_sets_year_for_annual` | 0.301 |
| [pass] | `tests.test_smoke.TestLicensing::test_activation_rejects_free_tier` | 0.196 |
| [pass] | `tests.test_smoke.TestLicensing::test_activation_requires_withdrawal_waiver` | 0.349 |
| [pass] | `tests.test_smoke.TestLicensing::test_affiliate_block_empty_when_no_partners` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_affiliate_block_format` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_affiliate_block_in_letter_text_is_static` | 0.273 |
| [pass] | `tests.test_smoke.TestLicensing::test_all_quotes_returns_pricing_tiers` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_annual_applies_20_percent_discount` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_annual_savings_vs_monthly` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_annual_total_matches_readme_base_tier` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_apply_token_persists_token_string` | 0.227 |
| [pass] | `tests.test_smoke.TestLicensing::test_build_pricing_rows_marks_recommended` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_build_pricing_rows_skips_family_above_cap` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_cancellation_includes_affiliate_suggestions` | 0.223 |
| [pass] | `tests.test_smoke.TestLicensing::test_chf_conversion_applies_swiss_vat` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_family_tier_flat_price` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_family_tier_rejects_too_many_persons` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_format_quote_de_mentions_savings` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_free_license_restricts_modules` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_free_tier_is_zero` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_gate_allows_everything_for_pro` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_gate_blocks_ai_capability_for_free` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_gate_blocks_pro_module_for_free` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_gate_open_modules_always_accessible` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_grandfathered_keeps_read_but_blocks_write` | 0.182 |
| [pass] | `tests.test_smoke.TestLicensing::test_grandfathering_migration_runs_once` | 0.192 |
| [pass] | `tests.test_smoke.TestLicensing::test_grandfathering_skipped_for_empty_db` | 0.161 |
| [pass] | `tests.test_smoke.TestLicensing::test_invalid_persons_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_issuer_signs_token_and_sends_mail` | 0.010 |
| [pass] | `tests.test_smoke.TestLicensing::test_issuer_skips_cancellations` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_lemon_signature_and_parse` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_lemon_uninteresting_event_returns_none` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_license_round_trip` | 0.200 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_defaults_to_free` | 0.194 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_drops_tampered_token` | 0.199 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_handles_corrupt_values` | 0.209 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_keeps_expired_token_for_grace` | 0.217 |
| [pass] | `tests.test_smoke.TestLicensing::test_mobile_pricing_has_markup` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_monthly_base_two_persons` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_monthly_charges_extra_persons` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_paddle_parse_event` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_paddle_signature_round_trip` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_paddle_unknown_price_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_pricing_onboarded_flag_persists` | 0.219 |
| [pass] | `tests.test_smoke.TestLicensing::test_pro_downgrades_after_grace_period` | 0.238 |
| [pass] | `tests.test_smoke.TestLicensing::test_pro_license_unlocks_everything` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_recommended_tier_picks_family_above_break_even` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_registry_pre_dispatch_hook_blocks_calls` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_event_for_pro_near_expiry` | 0.003 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_event_for_trial_near_end` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_event_in_grace_period` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_event_outside_warning_window` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_no_event_for_free` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_revocation_supersedes_grace_period` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_revoked_token_is_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_scheduler_picks_up_extra_event_sources` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_sidebar_indicator_strings` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_sign_token_auto_assigns_token_id` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_single_person_pays_base_price` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_subscription_info_for_free_has_no_subscription` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_subscription_info_for_pro_shows_dates` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_subscription_info_marks_grace_period` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_tier_status_for_free` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_tier_status_for_trial_shows_days_left` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_tier_status_in_grace_period` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_expired_raises_subclass_with_payload` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_rejects_expired` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_rejects_tampered_payload` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_sign_verify_round_trip` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_without_configured_pubkey_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_trial_is_not_reusable` | 0.273 |
| [pass] | `tests.test_smoke.TestLicensing::test_trial_starts_and_expires` | 0.194 |
| [pass] | `tests.test_smoke.TestLicensing::test_webhook_server_end_to_end` | 0.520 |
| [pass] | `tests.test_smoke.TestLicensing::test_webhook_server_rejects_bad_signature` | 0.518 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_fenced_json` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_fenced_without_lang` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_invalid_returns_empty` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_plain_json` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_prose_with_embedded_json` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmProposalValidation::test_missing_required_dropped` | 0.834 |
| [pass] | `tests.test_smoke.TestLlmProposalValidation::test_unknown_target_capability_dropped` | 0.961 |
| [pass] | `tests.test_smoke.TestModuleStatePersistence::test_disabled_module_id_persists` | 0.216 |
| [pass] | `tests.test_smoke.TestNotesModule::test_add_list_update_attach_delete` | 0.189 |
| [pass] | `tests.test_smoke.TestNotesModule::test_empty_title_rejected` | 0.197 |
| [pass] | `tests.test_smoke.TestNotesModule::test_invalid_entity_type_rejected` | 0.199 |
| [pass] | `tests.test_smoke.TestNotesModule::test_search_finds_notes` | 0.192 |
| [pass] | `tests.test_smoke.TestPrintFileNoShell::test_missing_file_returns_error` | 0.001 |
| [pass] | `tests.test_smoke.TestPrintFileNoShell::test_path_with_spaces_handled` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_db_path_default` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_db_path_with_profile` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_explicit_overrides_env` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_resolve_profile_uses_env` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_sanitize_profile` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_state_dir_default_and_profile` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_two_profiles_use_separate_files` | 0.371 |
| [pass] | `tests.test_smoke.TestProposalUpdate::test_update_blocked_after_accept` | 0.207 |
| [pass] | `tests.test_smoke.TestProposalUpdate::test_update_payload_replaces_value` | 0.205 |
| [pass] | `tests.test_smoke.TestProposalUpdate::test_update_then_accept_uses_new_payload` | 0.165 |
| [pass] | `tests.test_smoke.TestProposalsFlow::test_price_change_round_trip` | 0.226 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_invalid_date_rejected` | 0.206 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_negative_recurrence_rejected` | 0.191 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_none_recurrence_ok` | 0.173 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_positive_recurrence_ok` | 0.160 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_zero_recurrence_rejected` | 0.159 |
| [pass] | `tests.test_smoke.TestRegistry::test_capabilities_registered` | 0.152 |
| [pass] | `tests.test_smoke.TestRegistry::test_module_to_module_via_context` | 0.183 |
| [pass] | `tests.test_smoke.TestRegistry::test_unknown_capability_returns_error` | 0.187 |
| [pass] | `tests.test_smoke.TestRegistryGetCapability::test_returns_capability_object` | 0.151 |
| [pass] | `tests.test_smoke.TestRegistryGetCapability::test_returns_none_for_disabled_module` | 0.173 |
| [pass] | `tests.test_smoke.TestRegistryGetCapability::test_returns_none_for_unknown` | 0.182 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_assistant_ask_lock_serializes` | 0.158 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_bulk_complete_overdue_dispatches_individual_tasks` | 0.194 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_bulk_delete_archived_uses_repository_method` | 0.218 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_deleting_contract_cleans_attached_notes` | 0.205 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_geometry_validation` | 0.188 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_http_provider_has_read_all` | 4.253 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_export_folds_at_byte_boundary` | 0.280 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_import_rejects_nonexistent` | 0.233 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_import_rejects_path_outside_or_bad_extension` | 0.237 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_import_validates_recurrence` | 0.186 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_initial_lamport_ignores_other_devices` | 0.138 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_internal_capabilities_hidden_from_llm` | 0.145 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_notes_entity_id_zero_preserved` | 0.166 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_rrule_uses_yearly_for_365` | 0.189 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_sync_event_args_deep_copy` | 0.181 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_unescape_preserves_real_null_bytes` | 0.169 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_vcard_import_clamps_cadence` | 0.197 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_vcard_import_rejects_too_large` | 0.201 |
| [pass] | `tests.test_smoke.TestSearch::test_no_hit` | 0.829 |
| [pass] | `tests.test_smoke.TestSearch::test_search_finds_multiple_sources` | 0.259 |
| [pass] | `tests.test_smoke.TestSearch::test_short_query_rejected` | 0.217 |
| [pass] | `tests.test_smoke.TestSettings::test_db_value_overrides_default` | 0.156 |
| [pass] | `tests.test_smoke.TestSettings::test_defaults_when_empty` | 0.188 |
| [pass] | `tests.test_smoke.TestSettings::test_env_overrides_db` | 0.185 |
| [pass] | `tests.test_smoke.TestSettings::test_secret_is_not_persisted` | 0.180 |
| [pass] | `tests.test_smoke.TestSmtpWiring::test_smtp_config_from_app_config` | 0.001 |
| [pass] | `tests.test_smoke.TestSqlCipherValidation::test_nul_byte_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestSqlCipherValidation::test_too_short_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestStatistics::test_contracts_overview_top_3` | 0.226 |
| [pass] | `tests.test_smoke.TestStatistics::test_expenses_per_category_aggregates` | 0.216 |
| [pass] | `tests.test_smoke.TestStatistics::test_expenses_per_month_returns_buckets` | 0.217 |
| [pass] | `tests.test_smoke.TestStatistics::test_rejects_zero_months` | 0.223 |
| [pass] | `tests.test_smoke.TestStatistics::test_yearly_summary` | 0.240 |
| [pass] | `tests.test_smoke.TestSyncCompaction::test_compact_drops_oldest` | 0.032 |
| [pass] | `tests.test_smoke.TestSyncExpandedCapabilities::test_contract_replays_on_other_device` | 0.412 |
| [pass] | `tests.test_smoke.TestSyncReentry::test_non_synced_outer_lets_nested_log` | 0.235 |
| [pass] | `tests.test_smoke.TestSyncReentry::test_synced_outer_suppresses_synced_nested` | 0.209 |
| [pass] | `tests.test_smoke.TestSyncServerCompaction::test_server_drops_oldest_when_over_limit` | 0.583 |
| [pass] | `tests.test_smoke.TestSyncServerTls::test_serve_with_bad_cert_path_raises` | 0.004 |
| [pass] | `tests.test_smoke.TestThreadSafety::test_concurrent_dispatch` | 0.641 |
| [pass] | `tests.test_smoke.TestUtcTimestamps::test_event_timestamp_has_utc_marker` | 0.387 |
| [pass] | `tests.test_smoke.TestUtcTimestampsInDb::test_assistant_log_uses_utc` | 0.218 |
| [pass] | `tests.test_smoke.TestUtcTimestampsInDb::test_contract_created_at_uses_utc` | 0.203 |
| [pass] | `tests.test_smoke.TestVCardExport::test_export_creates_valid_vcard` | 0.187 |
| [pass] | `tests.test_smoke.TestVCardImportRoundTrip::test_roundtrip_preserves_rhythmus` | 0.365 |
| [pass] | `tests.test_smoke.TestYearlyPdfReport::test_pdf_report_produced` | 0.198 |
| [skip] | `tests.test_integration.TestGeminiRealApi::test_simple_ask_returns_text` | 0.000 |
| [skip] | `tests.test_integration.TestSqlCipherRealRoundTrip::test_encrypt_write_close_reopen` | 0.001 |
| [skip] | `tests.test_property.TestPropertyBasedSkipped::test_skipped` | 0.001 |

## Mapping zu Anhang A-K (TESTING.md)

| Anhang | Inhalt | Quelle im Repo |
| --- | --- | --- |
| A | Vollstaendiges Testkonzept | `TESTING.md` |
| B | Testarchitektur            | `tests/concept/` |
| C | Pairwise-Matrix            | `tests/concept/reports/pairwise-matrix.tsv` |
| D | Rollen-/Mitglieder-TCs     | `tests/concept/test_roles_permissions.py`, `tests/concept/test_members_scenarios.py` |
| E | Aufgaben-/Funktions-TCs    | `tests/concept/test_pairwise_matrix.py` |
| F | 14-Tage-Testplan           | `TESTING.md` Abschnitt 7 / Anhang F |
| G | Tester-Onboarding          | `TESTING.md` Anhang G |
| H | Feedback-/Fehlerberichte   | `TESTING.md` Anhang H |
| I | CI/CD-Pipeline             | `TESTING.md` Anhang I + `tools/test_protocol.py` |
| J | Go/No-Go-Kriterien         | `tests/concept/test_release_gate.py` |
| K | Massnahmenplan             | `TESTING.md` Anhang K |

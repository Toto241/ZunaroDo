# Test-Protokoll

- Datum: 2026-06-04 15:19:43 UTC
- Host: Toto241 (Windows-10-10.0.26200-SP0)
- Python: 3.11.9
- Target: `tests`
- Laufzeit pytest: 186.45 s

**Entscheidung:** GO

## Gesamtuebersicht

| Status | Anzahl |
| --- | ---: |
| passed | 1488 |
| failed | 0 |
| error | 0 |
| skipped | 6 |
| **gesamt** | **1494** |
| Dauer (Summe) | 183.76 s |

## Abdeckung nach Konzept-Bereich (Anhang)

| Bereich (Anhang) | Tests | passed | failed | error | skipped | Dauer (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kapitel 2 / Anhang D - Mitglieder-Szenarien | 18 | 18 | 0 | 0 | 0 | 64.30 |
| Anhang D - Rollen- und Berechtigungsmatrix | 69 | 69 | 0 | 0 | 0 | 4.52 |
| Kapitel 3 / Anhang C - Pairwise-Matrix | 13 | 13 | 0 | 0 | 0 | 4.49 |
| Kapitel 8 - Property-/Fuzz-Tests | 29 | 29 | 0 | 0 | 0 | 10.20 |
| Teil II Abschnitt 11 - Negativtests | 48 | 48 | 0 | 0 | 0 | 10.38 |
| Teil II Abschnitt 12 - Datenschutztests | 319 | 319 | 0 | 0 | 0 | 2.75 |
| Teil II Abschnitt 11.3 D - Security-Negativtests | 22 | 22 | 0 | 0 | 0 | 0.03 |
| Play-Store-Sync (tools/playstore_sync.py) | 29 | 29 | 0 | 0 | 0 | 0.19 |
| Anhang J + J2 - Release-Gate | 356 | 356 | 0 | 0 | 0 | 24.81 |

## Ergebnisse pro Testdatei

| Datei | Tests | passed | failed | error | skipped | Dauer (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TestAgendaOverview | 6 | 6 | 0 | 0 | 0 | 1.06 |
| TestAssistantLogRotation | 1 | 1 | 0 | 0 | 0 | 0.32 |
| TestAutoBackup | 2 | 2 | 0 | 0 | 0 | 0.50 |
| TestBackupAndRestore | 3 | 3 | 0 | 0 | 0 | 0.61 |
| TestBackupSqlCipherPath | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestBirthdayEventsDoesNotCrashOnLeapDay | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestBirthdayInYear | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestBuildHtml | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestBuildOrderPayload | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestBuildSearchArgs | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestBulkInsertPerformance | 3 | 3 | 0 | 0 | 0 | 6.84 |
| TestBulkOperations | 3 | 3 | 0 | 0 | 0 | 0.57 |
| TestCalendarNoMutation | 1 | 1 | 0 | 0 | 0 | 0.17 |
| TestCalendarRecurrenceGuard | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestCheck | 3 | 3 | 0 | 0 | 0 | 0.04 |
| TestCheckConsistency | 4 | 4 | 0 | 0 | 0 | 0.02 |
| TestCheckDataDeletion | 3 | 3 | 0 | 0 | 0 | 0.02 |
| TestCheckDemoData | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestCheckI18n | 1 | 1 | 0 | 0 | 0 | 0.01 |
| TestCheckPermissions | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestCheckSdkLevels | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestCheckSecrets | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestCheckVersioning | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestClosedTestGate | 7 | 7 | 0 | 0 | 0 | 0.03 |
| TestCodeSmells | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestCompleteTaskCatchUp | 1 | 1 | 0 | 0 | 0 | 0.20 |
| TestConversationHistory | 1 | 1 | 0 | 0 | 0 | 0.17 |
| TestCsvExport | 2 | 2 | 0 | 0 | 0 | 0.42 |
| TestCsvImportRejectsMalformed | 6 | 6 | 0 | 0 | 0 | 1.07 |
| TestCsvImportRoundTrip | 3 | 3 | 0 | 0 | 0 | 0.84 |
| TestCuratedQuality | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestDashboardSummary | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestDataDeletionReachable | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestDataSafetyOptionalFeatures | 4 | 4 | 0 | 0 | 0 | 0.02 |
| TestDayStructurePersistence | 1 | 1 | 0 | 0 | 0 | 0.18 |
| TestDaysUntil | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestDeadlineCalculationPerformance | 1 | 1 | 0 | 0 | 0 | 0.14 |
| TestDefaultSecureStore | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestDeleteAllUserData | 1 | 1 | 0 | 0 | 0 | 0.43 |
| TestDeleteCapabilities | 4 | 4 | 0 | 0 | 0 | 0.70 |
| TestDeletionSupported | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestDestructiveFlags | 1 | 1 | 0 | 0 | 0 | 0.17 |
| TestDetectDeviceLanguage | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestDetectTrackingSdks | 3 | 3 | 0 | 0 | 0 | 0.02 |
| TestDiagnose | 1 | 1 | 0 | 0 | 0 | 1.08 |
| TestDisabledModuleSurfaced | 1 | 1 | 0 | 0 | 0 | 0.15 |
| TestDistinctValues | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestEncryption | 2 | 2 | 0 | 0 | 0 | 0.19 |
| TestEuRegistry | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestExportJson | 2 | 2 | 0 | 0 | 0 | 1.59 |
| TestFindPlaceholders | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestFingerprint | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestFormatCurrency | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestFormatMarkdown | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestGeminiAssistantStub | 2 | 2 | 0 | 0 | 0 | 0.49 |
| TestGeminiRealApi | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestGenerate | 3 | 3 | 0 | 0 | 0 | 0.02 |
| TestGenerateLocalizations | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestGroupByModule | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestGuiBootSmoke | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestGuiImports | 7 | 7 | 0 | 0 | 0 | 0.02 |
| TestHasCapabilityHonorsDisabled | 2 | 2 | 0 | 0 | 0 | 0.31 |
| TestHeadlessApp | 5 | 5 | 0 | 0 | 0 | 0.98 |
| TestHkdf | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestHttpSyncRoundTrip | 1 | 1 | 0 | 0 | 0 | 0.52 |
| TestHttpsSyncServer | 1 | 1 | 0 | 0 | 0 | 0.69 |
| TestI18n | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestI18nClass | 8 | 8 | 0 | 0 | 0 | 0.01 |
| TestI18nSyncTool | 3 | 3 | 0 | 0 | 0 | 0.02 |
| TestIcalExport | 1 | 1 | 0 | 0 | 0 | 0.17 |
| TestIcalImportRoundTrip | 2 | 2 | 0 | 0 | 0 | 0.48 |
| TestIcsImportDstRecurrence | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestIdentity | 7 | 7 | 0 | 0 | 0 | 0.01 |
| TestImapAbruf | 1 | 1 | 0 | 0 | 0 | 0.18 |
| TestInMemorySecureStore | 8 | 8 | 0 | 0 | 0 | 0.01 |
| TestInboxExtractText | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestInputValidation | 6 | 6 | 0 | 0 | 0 | 1.24 |
| TestKeyringSecureStore | 4 | 4 | 0 | 0 | 0 | 0.09 |
| TestLamportCrdt | 3 | 3 | 0 | 0 | 0 | 0.19 |
| TestLanguageMenuItems | 7 | 7 | 0 | 0 | 0 | 0.02 |
| TestLicensing | 78 | 78 | 0 | 0 | 0 | 5.07 |
| TestLlmJsonParsing | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestLlmProposalValidation | 2 | 2 | 0 | 0 | 0 | 0.33 |
| TestLocaleFilesIntegrity | 5 | 5 | 0 | 0 | 0 | 0.03 |
| TestMainImports | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestMobileBootSmoke | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestMobileScreenCapabilities | 1 | 1 | 0 | 0 | 0 | 0.18 |
| TestModuleStatePersistence | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestNormalizeLanguage | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestNormalizePriority | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestNotesListingPerformance | 1 | 1 | 0 | 0 | 0 | 5.62 |
| TestNotesModule | 4 | 4 | 0 | 0 | 0 | 0.64 |
| TestNotifierGracefulDegradation | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestOcrParsing | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestOrderSchemaMigration | 1 | 1 | 0 | 0 | 0 | 0.12 |
| TestOrphanOwnerId | 4 | 4 | 0 | 0 | 0 | 0.68 |
| TestPairingFailures | 5 | 5 | 0 | 0 | 0 | 0.09 |
| TestPairingHappyPath | 3 | 3 | 0 | 0 | 0 | 0.09 |
| TestParseBuildozerSpec | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestPostNotificationsPermission | 4 | 4 | 0 | 0 | 0 | 0.02 |
| TestPresenters | 18 | 18 | 0 | 0 | 0 | 3.31 |
| TestPrintFileNoShell | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestPrinten | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestPriorityAndCategoryFilters | 6 | 6 | 0 | 0 | 0 | 1.06 |
| TestProfile | 7 | 7 | 0 | 0 | 0 | 0.29 |
| TestProfilesManager | 7 | 7 | 0 | 0 | 0 | 0.04 |
| TestProfilesModule | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestPropertyBasedSkipped | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestProposalCreatedAt | 1 | 1 | 0 | 0 | 0 | 0.15 |
| TestProposalUpdate | 3 | 3 | 0 | 0 | 0 | 0.65 |
| TestProposalsFlow | 1 | 1 | 0 | 0 | 0 | 0.16 |
| TestPurgeDirectories | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestRealRepo | 6 | 6 | 0 | 0 | 0 | 0.06 |
| TestRealRepoFallback | 4 | 4 | 0 | 0 | 0 | 0.01 |
| TestRecurrenceValidation | 5 | 5 | 0 | 0 | 0 | 0.88 |
| TestRegistry | 3 | 3 | 0 | 0 | 0 | 0.50 |
| TestRegistryGetCapability | 3 | 3 | 0 | 0 | 0 | 0.55 |
| TestRelativeWhen | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestReminderPersistence | 5 | 5 | 0 | 0 | 0 | 0.02 |
| TestReminderTriggering | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestReportFormats | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestRequirementsCoverage | 4 | 4 | 0 | 0 | 0 | 0.13 |
| TestResolveLanguage | 7 | 7 | 0 | 0 | 0 | 0.01 |
| TestReviewFixes | 18 | 18 | 0 | 0 | 0 | 7.19 |
| TestRunChecksIntegration | 2 | 2 | 0 | 0 | 0 | 0.20 |
| TestSandboxDataDirs | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestSearch | 3 | 3 | 0 | 0 | 0 | 0.62 |
| TestSearchFilters | 7 | 7 | 0 | 0 | 0 | 1.47 |
| TestSecretsDoNotLeak | 1 | 1 | 0 | 0 | 0 | 0.02 |
| TestSelfSignedCert | 4 | 3 | 0 | 0 | 1 | 0.29 |
| TestSettings | 4 | 4 | 0 | 0 | 0 | 0.68 |
| TestSmtpVersand | 4 | 4 | 0 | 0 | 0 | 0.01 |
| TestSmtpWiring | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestSoftDeletedOwnerName | 1 | 1 | 0 | 0 | 0 | 0.21 |
| TestSqlCipherRealRoundTrip | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestSqlCipherValidation | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestStatistics | 5 | 5 | 0 | 0 | 0 | 1.07 |
| TestSyncCompaction | 1 | 1 | 0 | 0 | 0 | 0.03 |
| TestSyncConflictDeterminism | 2 | 2 | 0 | 0 | 0 | 0.42 |
| TestSyncExpandedCapabilities | 1 | 1 | 0 | 0 | 0 | 0.40 |
| TestSyncReentry | 2 | 2 | 0 | 0 | 0 | 0.38 |
| TestSyncReliability | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestSyncReplayThreadSafety | 1 | 1 | 0 | 0 | 0 | 0.17 |
| TestSyncRuntime | 4 | 4 | 0 | 0 | 0 | 0.79 |
| TestSyncServerCompaction | 1 | 1 | 0 | 0 | 0 | 0.58 |
| TestSyncServerTls | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestThreadSafety | 1 | 1 | 0 | 0 | 0 | 0.66 |
| TestTranscript | 7 | 7 | 0 | 0 | 0 | 0.01 |
| TestTranslationResolution | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestTruncate | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestUiText | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestUrgencyColor | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestUtcTimestamps | 1 | 1 | 0 | 0 | 0 | 0.18 |
| TestUtcTimestampsInDb | 2 | 2 | 0 | 0 | 0 | 0.33 |
| TestVCardExport | 1 | 1 | 0 | 0 | 0 | 0.18 |
| TestVCardImportRoundTrip | 1 | 1 | 0 | 0 | 0 | 0.33 |
| TestValidateLocalizations | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestWeekAgenda | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestWipeAllData | 3 | 3 | 0 | 0 | 0 | 1.49 |
| TestYearlyPdfReport | 1 | 1 | 0 | 0 | 0 | 0.21 |
| test_build_status | 17 | 17 | 0 | 0 | 0 | 2.98 |
| test_control_panel | 14 | 14 | 0 | 0 | 0 | 1.47 |
| test_dashboard_generator | 20 | 20 | 0 | 0 | 0 | 4.86 |
| test_datadir | 12 | 12 | 0 | 0 | 0 | 0.08 |
| test_gitignore_completeness | 82 | 82 | 0 | 0 | 0 | 1.19 |
| test_gui_free_tier_boot | 2 | 2 | 0 | 0 | 0 | 6.23 |
| test_gui_refresh_guards | 16 | 16 | 0 | 0 | 0 | 0.96 |
| test_gui_widget_guards | 3 | 3 | 0 | 0 | 0 | 5.15 |
| test_md_to_html | 15 | 15 | 0 | 0 | 0 | 0.01 |
| test_members_scenarios | 18 | 18 | 0 | 0 | 0 | 64.30 |
| test_negative_inputs | 40 | 40 | 0 | 0 | 0 | 7.28 |
| test_negative_network | 8 | 8 | 0 | 0 | 0 | 3.10 |
| test_negative_security | 22 | 22 | 0 | 0 | 0 | 0.03 |
| test_pairwise_matrix | 13 | 13 | 0 | 0 | 0 | 4.49 |
| test_playstore_sync | 29 | 29 | 0 | 0 | 0 | 0.19 |
| test_privacy_data_rights | 10 | 10 | 0 | 0 | 0 | 2.22 |
| test_privacy_scan | 309 | 309 | 0 | 0 | 0 | 0.54 |
| test_properties_concept | 29 | 29 | 0 | 0 | 0 | 10.20 |
| test_protocol_generator | 5 | 5 | 0 | 0 | 0 | 0.07 |
| test_release_gate | 10 | 10 | 0 | 0 | 0 | 1.69 |
| test_release_gate_extended | 172 | 172 | 0 | 0 | 0 | 0.20 |
| test_roles_permissions | 69 | 69 | 0 | 0 | 0 | 4.52 |

## Vollstaendige Test-Liste

| Status | Test-ID | Dauer (s) |
| --- | --- | ---: |
| [pass] | `tests.concept.test_build_status::test_build_center_in_dashboard_html` | 0.375 |
| [pass] | `tests.concept.test_build_status::test_build_center_links_point_to_real_scripts` | 0.378 |
| [pass] | `tests.concept.test_build_status::test_build_center_section_in_index_html` | 0.279 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-android.bat]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-android.sh]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-desktop.bat]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-desktop.sh]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-ios.sh]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_buildozer_spec_present_for_android` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_each_item_has_required_fields` | 0.281 |
| [pass] | `tests.concept.test_build_status::test_gather_returns_three_platforms` | 0.276 |
| [pass] | `tests.concept.test_build_status::test_index_build_center_renders_three_cards` | 0.276 |
| [pass] | `tests.concept.test_build_status::test_index_build_center_uses_clipboard_helper` | 0.278 |
| [pass] | `tests.concept.test_build_status::test_main_json_runs` | 0.278 |
| [pass] | `tests.concept.test_build_status::test_main_plain_text_runs` | 0.282 |
| [pass] | `tests.concept.test_build_status::test_pyinstaller_spec_present_for_desktop` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_to_dict_is_json_serializable` | 0.275 |
| [pass] | `tests.concept.test_control_panel::test_actions_build_lists_three_platforms_indirectly` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_actions_build_uses_existing_scripts` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_actions_playstore_complete` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_actions_tests_call_python_modules` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_actions_tests_complete` | 0.008 |
| [pass] | `tests.concept.test_control_panel::test_command_runner_busy_flag` | 0.413 |
| [pass] | `tests.concept.test_control_panel::test_command_runner_returns_nonzero_on_failure` | 0.109 |
| [pass] | `tests.concept.test_control_panel::test_command_runner_streams_and_signals_done` | 0.077 |
| [pass] | `tests.concept.test_control_panel::test_destructive_actions_have_confirm_prompt` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_link_targets_are_known_repo_paths` | 0.003 |
| [pass] | `tests.concept.test_control_panel::test_links_point_to_known_paths` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_start_bat_checks_customtkinter` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_start_bat_invokes_control_panel` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_window_can_be_constructed_and_destroyed` | 0.856 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket0-go]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket1-block]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket2-block]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket3-hold]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket4-unknown]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_decision_status_mapping` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_default_paths_inside_reports_dir` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_failure_section_shows_when_records_failed` | 0.331 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_contains_all_records` | 0.374 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_does_not_contain_nested_anchors` | 0.370 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_escapes_html_in_test_id` | 0.334 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_has_kpi_for_each_marker` | 0.375 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_has_navigation` | 0.373 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_is_self_contained` | 0.372 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_links_to_companion_artifacts` | 0.365 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_renders_decision_pill` | 0.405 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_renders_skipped_as_hold` | 0.366 |
| [pass] | `tests.concept.test_dashboard_generator::test_main_handles_missing_input` | 0.003 |
| [pass] | `tests.concept.test_dashboard_generator::test_main_runs_against_real_protocol` | 0.458 |
| [pass] | `tests.concept.test_dashboard_generator::test_render_dashboard_is_deterministic` | 0.722 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.aab]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.apk]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.db]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.dll]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.dylib]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.exe]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.ipa]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.keystore]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.pyc]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.pyd]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.so]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[*.sqlite]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[.DS_Store]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[.buildozer/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[.coverage]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[.idea/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[.mypy_cache/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[.pytest_cache/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[.venv/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[.vscode/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[DerivedData/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[Thumbs.db]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[__pycache__/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[ausgaben/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[backups/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[bin/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[build/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[dist/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[htmlcov/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[logs/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[playstore.local.json]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_contains_pattern[xcuserdata/]` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_has_pyinstaller_section_comment` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_gitignore_not_empty` | 0.001 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.AppImage]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.aab]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.apk]` | 0.029 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.deb]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.dll]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.dmg]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.dylib]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.exe]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.ipa]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.jks]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.keystore]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.msi]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.pyd]` | 0.031 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.rpm]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.so]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_dist_or_build_folder_tracked` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[.DS_Store]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[.buildozer/android/platform/build.cfg]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[.coverage]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[.pytest_cache/v/cache/lastfailed]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[DerivedData/Build/Products/Debug.app/Foo]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[Thumbs.db]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[ZunaroDo-ios/Pods/Manifest.lock]` | 0.025 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[ZunaroDo-ios/xcuserdata/torst.xcuserdatad/UserInterfaceState.xcuserstate]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[ZunaroDo.exe]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[alltagshelfer.db]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[ausgaben/2026-05.pdf]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[backups/2026-05.tar.gz]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[bin/alltagshelfer-0.9.0-arm64-v8a-debug.apk]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[build/anything/at/any/depth.py]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[build/foo.txt]` | 0.025 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/ZunaroDo/ZunaroDo.exe]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/ZunaroDo/_internal/_tcl_data/tcl8.6/init.tcl]` | 0.025 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/ZunaroDo/_internal/cryptography/hazmat/_oid.cpython-311.dll]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/ZunaroDo/_internal/python311.dll]` | 0.025 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/something.dmg]` | 0.026 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[htmlcov/index.html]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[logs/app.log]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[playstore.local.json]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.AppImage]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.aab]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.deb]` | 0.024 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.ipa]` | 0.026 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.jks]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.keystore]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[test.sqlite]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[tools/__pycache__/dashboard.cpython-311.pyc]` | 0.023 |
| [pass] | `tests.concept.test_gitignore_completeness::test_playstore_local_json_not_tracked` | 0.023 |
| [pass] | `tests.concept.test_gui_free_tier_boot::test_gui_boots_in_free_tier_without_crash` | 3.168 |
| [pass] | `tests.concept.test_gui_free_tier_boot::test_gui_boots_with_default_license_too` | 3.063 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_all_refresh_methods_are_guarded` | 0.053 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_calendar]` | 0.074 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_contracts]` | 0.048 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_dashboard]` | 0.048 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_finance]` | 0.048 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_history]` | 0.061 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_inbox]` | 0.045 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_members]` | 0.079 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_module_admin]` | 0.091 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_orders]` | 0.049 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_shopping]` | 0.073 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_social]` | 0.046 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_statistics]` | 0.043 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_status]` | 0.069 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_tasks]` | 0.048 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_methods_exist` | 0.081 |
| [pass] | `tests.concept.test_gui_widget_guards::test_can_load_gui_module_source` | 0.064 |
| [pass] | `tests.concept.test_gui_widget_guards::test_chat_methods_are_guarded` | 0.565 |
| [pass] | `tests.concept.test_gui_widget_guards::test_methods_in_init_path_have_widget_guards` | 4.518 |
| [pass] | `tests.concept.test_md_to_html::test_doc_wrapper_back_link` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_doc_wrapper_includes_dashboard_css` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_escapes_html_in_paragraphs` | 0.000 |
| [pass] | `tests.concept.test_md_to_html::test_inline_code_protects_from_bold` | 0.000 |
| [pass] | `tests.concept.test_md_to_html::test_renders_blockquote` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_bold_italic_code` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_fenced_code_block` | 0.000 |
| [pass] | `tests.concept.test_md_to_html::test_renders_h2_to_h6` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_headings_with_anchors` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_hr` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_link` | 0.000 |
| [pass] | `tests.concept.test_md_to_html::test_renders_ordered_list` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_paragraphs` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_table` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_unordered_list` | 0.001 |
| [pass] | `tests.concept.test_members_scenarios::test_M01_single_owner_no_rotation` | 0.414 |
| [pass] | `tests.concept.test_members_scenarios::test_M02_minimal_team_two_members` | 0.689 |
| [pass] | `tests.concept.test_members_scenarios::test_M05_meets_play_minimum_12` | 4.323 |
| [pass] | `tests.concept.test_members_scenarios::test_M06_scales_to_twenty_plus` | 5.929 |
| [pass] | `tests.concept.test_members_scenarios::test_M07_mixed_status_distribution` | 4.021 |
| [pass] | `tests.concept.test_members_scenarios::test_M08_invited_only_owner_active` | 0.592 |
| [pass] | `tests.concept.test_members_scenarios::test_M09_reactivation_restores_member` | 1.114 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-01]` | 0.408 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-02]` | 0.749 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-03]` | 1.629 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-04]` | 3.518 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-05]` | 4.337 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-06]` | 5.643 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-07]` | 4.138 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-08]` | 0.631 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-09]` | 1.023 |
| [pass] | `tests.concept.test_members_scenarios::test_get_events_handles_all_sizes` | 23.445 |
| [pass] | `tests.concept.test_members_scenarios::test_remove_and_readd_preserves_distinct_id` | 1.695 |
| [pass] | `tests.concept.test_negative_inputs::test_NA02_long_contract_name_does_not_break_listing` | 0.160 |
| [pass] | `tests.concept.test_negative_inputs::test_NA02_long_member_name_is_stored_or_rejected[10000]` | 0.176 |
| [pass] | `tests.concept.test_negative_inputs::test_NA02_long_member_name_is_stored_or_rejected[1024]` | 0.183 |
| [pass] | `tests.concept.test_negative_inputs::test_NA02_long_member_name_is_stored_or_rejected[65536]` | 0.148 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description["Anna' DROP"]` | 0.147 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['  trailing space   ']` | 0.183 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description[' ']` | 0.158 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['<script>alert(1)</scrip]` | 0.183 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['Anna \U0001f600']` | 0.197 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['Anna\\nMehrzeilig']` | 0.216 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['Anna\\x00Nachher']` | 0.184 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['\\u202earabicRTL']` | 0.202 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['\u0410\u043d\u043d\u0430 \u0418\u0432\u0430\u043d\u043e\u0432\u0430']` | 0.158 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['\u5c71\u7530\u592a\u90ce']` | 0.165 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name["Anna' DROP"]` | 0.154 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['  trailing space   ']` | 0.211 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name[' ']` | 0.188 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['<script>alert(1)</scrip]` | 0.194 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['Anna \U0001f600']` | 0.167 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['Anna\\nMehrzeilig']` | 0.189 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['Anna\\x00Nachher']` | 0.193 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['\\u202earabicRTL']` | 0.213 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['\u0410\u043d\u043d\u0430 \u0418\u0432\u0430\u043d\u043e\u0432\u0430']` | 0.143 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['\u5c71\u7530\u592a\u90ce']` | 0.185 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[%27%20OR%201=1%20--%]` | 0.191 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields['); DELETE FROM cont]` | 0.176 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[1' OR '1'='1]` | 0.160 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[Anna"; UPDATE family]` | 0.174 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[Anna'; DROP TABLE fa]` | 0.139 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[Anna\\'; SELECT * FRO]` | 0.201 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[%27%20OR%201=1%20--%]` | 0.198 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal['); DELETE FROM cont]` | 0.200 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[1' OR '1'='1]` | 0.202 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[Anna"; UPDATE family]` | 0.190 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[Anna'; DROP TABLE fa]` | 0.179 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[Anna\\'; SELECT * FRO]` | 0.212 |
| [pass] | `tests.concept.test_negative_inputs::test_NA05_double_member_is_idempotent_or_distinct_ids` | 0.216 |
| [pass] | `tests.concept.test_negative_inputs::test_NA11_invalid_param_type_does_not_crash` | 0.152 |
| [pass] | `tests.concept.test_negative_inputs::test_NA11_missing_required_param_returns_friendly_error` | 0.207 |
| [pass] | `tests.concept.test_negative_inputs::test_NA11_unknown_capability_returns_friendly_error` | 0.181 |
| [pass] | `tests.concept.test_negative_network::test_NB01_unreachable_server_does_not_corrupt_state` | 2.037 |
| [pass] | `tests.concept.test_negative_network::test_NB04_garbage_response_is_handled` | 0.516 |
| [pass] | `tests.concept.test_negative_network::test_NB04_server_500_does_not_silently_succeed` | 0.533 |
| [pass] | `tests.concept.test_negative_network::test_NB06_corrupt_log_lines_are_skipped` | 0.003 |
| [pass] | `tests.concept.test_negative_network::test_NB06_offline_then_sync_round_trips_events` | 0.006 |
| [pass] | `tests.concept.test_negative_network::test_NB07_lww_orders_by_lamport_then_time` | 0.005 |
| [pass] | `tests.concept.test_negative_network::test_lamport_observe_clamps_negative_input` | 0.001 |
| [pass] | `tests.concept.test_negative_network::test_sync_event_from_dict_handles_missing_fields` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_ND04_swapped_signing_key_is_rejected` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_ND04_tampered_payload_is_rejected` | 0.003 |
| [pass] | `tests.concept.test_negative_security::test_ND04_tampered_signature_is_rejected` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_ND06_legit_path_accepted` | 0.002 |
| [pass] | `tests.concept.test_negative_security::test_ND06_path_traversal_is_blocked` | 0.003 |
| [pass] | `tests.concept.test_negative_security::test_ND10_escape_roundtrip_is_safe[Anna\nBEGIN:VCALENDAR\nMaliciousField:1\nEND:VCALENDAR]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_ND10_escape_roundtrip_is_safe[\u200b zero-width space]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_ND10_escape_roundtrip_is_safe[title with \\ backslash]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_ND10_escape_roundtrip_is_safe[title,with,commas]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_ND10_escape_roundtrip_is_safe[title;]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE01_invalid_token_strings[...]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE01_invalid_token_strings[.]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE01_invalid_token_strings[AAAA.BBBB]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE01_invalid_token_strings[]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE01_invalid_token_strings[no-dot-here]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE01_invalid_token_strings[x.y.z.too.many.dots]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE01_invalid_token_strings[{}.signature]` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE02_expired_token_raises_token_expired` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE02_expired_token_still_provides_payload` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE03_empty_pubkey_is_rejected` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_NE03_garbage_pubkey_is_rejected` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_token_id_auto_populated_for_revocation` | 0.001 |
| [pass] | `tests.concept.test_pairwise_matrix::test_artifact_tsv_written` | 0.001 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_covers_at_least_95_percent_of_pairs` | 0.006 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_has_acceptable_size` | 0.001 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_is_deterministic` | 1.754 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_respects_constraints` | 0.863 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[0]` | 0.160 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[100]` | 0.192 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[125]` | 0.200 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[150]` | 0.362 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[175]` | 0.337 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[25]` | 0.163 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[50]` | 0.225 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[75]` | 0.224 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_export_writes_snapshot` | 0.044 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_init_writes_yaml` | 0.010 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_push_aborts_on_invalid` | 0.009 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_push_dry_run_and_pull_via_mock` | 0.043 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_sample_prints_yaml` | 0.014 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_validate_on_sample` | 0.017 |
| [pass] | `tests.concept.test_playstore_sync::test_default_yaml_in_repo_is_valid` | 0.026 |
| [pass] | `tests.concept.test_playstore_sync::test_diff_keys_empty_when_equal` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_diff_keys_reports_added_and_removed` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_diff_keys_reports_changed_strings` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_export_markdown_contains_all_sections` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_export_markdown_shows_length_counters` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_init_from_repo_has_required_top_level` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_init_from_repo_picks_up_buildozer_settings` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_invalid_package_name_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_invalid_release_status_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_merge_keeps_local_when_remote_empty` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_merge_prefers_remote_when_not_empty` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_missing_internet_permission_is_warning` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_missing_top_level_keys_are_errors` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_mock_dry_run_does_not_modify_state` | 0.004 |
| [pass] | `tests.concept.test_playstore_sync::test_mock_pull_unknown_package_raises` | 0.003 |
| [pass] | `tests.concept.test_playstore_sync::test_mock_roundtrip_persists_and_returns_identical` | 0.005 |
| [pass] | `tests.concept.test_playstore_sync::test_permission_overlap_declared_blocked_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_sample_config_validates_clean` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_too_long_full_description_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_too_long_short_description_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_too_long_title_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_user_fraction_out_of_range_is_error` | 0.001 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB02_purging_member_decouples_references` | 0.195 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_calendar-termine.csv-calendar]` | 0.209 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_contracts-vertraege.csv-contracts]` | 0.201 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_expenses-ausgaben.csv-expenses]` | 0.215 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_family-haushalt.csv-family]` | 0.239 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_social-kontakte.csv-social]` | 0.220 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_export_all_produces_parseable_artifacts` | 0.204 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB04_soft_delete_hides_then_restore_brings_back` | 0.218 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB06_dropping_db_file_removes_all_data` | 0.329 |
| [pass] | `tests.concept.test_privacy_data_rights::test_audit_log_format_does_not_leak_pii` | 0.189 |
| [pass] | `tests.concept.test_privacy_scan::test_JG03_min_sdk_is_supported` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JG03_target_sdk_meets_play_minimum` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[__main__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[assistant.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[core/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[core/interface.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[database.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[diagnose.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[gui.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[main.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/app.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/headless_app.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/presenters.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/export_data.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/license.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/more.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/ui_text.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[models.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/family.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/inbox.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/overview.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/profiles.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/social.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/data_deletion.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/datadir.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/escaping.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/export.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/gemini.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/i18n.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/ical.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/import_csv.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/io_validation.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/legal.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/license_events.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/license_gate.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/license_token.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/license_ui.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/licensing.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/llm.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/logging_setup.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/notifier.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/ocr.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/open_file.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/output.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/pairing/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/pairing/identity.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/pairing/kdf.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/pairing/secure_store.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/pairing/session.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/pairing/transcript.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/payment.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/payment_adapter_lemon.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/payment_adapter_paddle.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/payment_issuer.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/payment_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/profile.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/reports.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/scheduler.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/sync.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/sync_runtime.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/sync_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/tls_certs.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/vcard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/_cap_translations.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/_cap_translations_extra.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/build_status.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/control_panel.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/data_safety.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/gen_api_doc.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/gen_cap_descriptions.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/gen_license.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/i18n_sync.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/legal_status.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/md_to_html.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/payment_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/playstore_check.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/playstore_sync.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/privacy_policy.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/store_listing.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/test_protocol.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PA01_legal_docs_not_empty` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PA01_legal_docs_present[AGB.md]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PA01_legal_docs_present[DATENSCHUTZ.md]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PA01_legal_docs_present[IMPRESSUM.md]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PA01_legal_docs_present[WIDERRUF.md]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PA04_sdk_inventory_mentioned` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PB01_account_deletion_capability_exists` | 0.209 |
| [pass] | `tests.concept.test_privacy_scan::test_PC01_at_least_internet_declared` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PC01_only_whitelisted_permissions` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[__main__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[assistant.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[core/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[core/interface.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[database.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[diagnose.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[gui.py]` | 0.003 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[main.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/app.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/headless_app.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/presenters.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/export_data.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/license.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/more.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/ui_text.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[models.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/family.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/inbox.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/overview.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/profiles.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/social.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/data_deletion.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/datadir.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/escaping.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/export.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/gemini.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/i18n.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/ical.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/import_csv.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/io_validation.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/legal.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/license_events.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/license_gate.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/license_token.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/license_ui.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/licensing.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/llm.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/logging_setup.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/notifier.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/ocr.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/open_file.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/output.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/pairing/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/pairing/identity.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/pairing/kdf.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/pairing/secure_store.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/pairing/session.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/pairing/transcript.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/payment.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/payment_adapter_lemon.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/payment_adapter_paddle.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/payment_issuer.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/payment_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/profile.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/reports.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/scheduler.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/sync.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/sync_runtime.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/sync_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/tls_certs.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/vcard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/_cap_translations.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/_cap_translations_extra.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/build_status.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/control_panel.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/data_safety.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/gen_api_doc.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/gen_cap_descriptions.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/gen_license.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/i18n_sync.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/legal_status.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/md_to_html.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/payment_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/playstore_check.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/playstore_sync.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/privacy_policy.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/store_listing.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/test_protocol.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[__main__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[assistant.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[core/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[core/interface.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[database.py]` | 0.003 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[diagnose.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[gui.py]` | 0.005 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[main.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/app.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/headless_app.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/presenters.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/export_data.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/license.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/more.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/ui_text.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[models.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/family.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/inbox.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/overview.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/profiles.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/social.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/data_deletion.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/datadir.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/escaping.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/export.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/gemini.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/i18n.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/ical.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/import_csv.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/io_validation.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/legal.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/license_events.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/license_gate.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/license_token.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/license_ui.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/licensing.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/llm.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/logging_setup.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/notifier.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/ocr.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/open_file.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/output.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/pairing/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/pairing/identity.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/pairing/kdf.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/pairing/secure_store.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/pairing/session.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/pairing/transcript.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/payment.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/payment_adapter_lemon.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/payment_adapter_paddle.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/payment_issuer.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/payment_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/profile.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/reports.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/scheduler.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/sync.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/sync_runtime.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/sync_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/tls_certs.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/vcard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/_cap_translations.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/_cap_translations_extra.py]` | 0.004 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/build_status.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/control_panel.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/dashboard.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/data_safety.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/gen_api_doc.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/gen_cap_descriptions.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/gen_license.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/i18n_sync.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/legal_status.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/md_to_html.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/payment_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/playstore_check.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/playstore_sync.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/privacy_policy.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/store_listing.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/test_protocol.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD08_backup_flag_is_explicit` | 0.001 |
| [pass] | `tests.concept.test_properties_concept::test_P1_rotation_advances_one_step` | 4.286 |
| [pass] | `tests.concept.test_properties_concept::test_P2_overdue_task_rolls_forward_to_future` | 4.198 |
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
| [pass] | `tests.concept.test_properties_concept::test_P6_pairwise_deterministic` | 1.687 |
| [pass] | `tests.concept.test_protocol_generator::test_failure_protocol_is_no_go_not_stale_go` | 0.007 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_artifacts_present_after_run` | 0.010 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_classifies_and_decides` | 0.008 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_formats_markdown` | 0.040 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_parses_junit` | 0.008 |
| [pass] | `tests.concept.test_release_gate::test_J10_full_module_registry_assembles` | 0.819 |
| [pass] | `tests.concept.test_release_gate::test_J1_version_code_is_positive_integer` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J2_privacy_documents_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J3_license_file_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J4_playstore_doc_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J5_testing_doc_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J6_concept_modules_import` | 0.000 |
| [pass] | `tests.concept.test_release_gate::test_J7_pairwise_matrix_has_full_coverage` | 0.860 |
| [pass] | `tests.concept.test_release_gate::test_J8_permission_matrix_is_complete` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J9_member_profiles_present` | 0.000 |
| [pass] | `tests.concept.test_release_gate_extended::test_JG04_playstore_doc_covers_section[Closed]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JG04_playstore_doc_covers_section[Datenschutz]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JG04_playstore_doc_covers_section[Produktionsfreigabe]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JG04_playstore_doc_covers_section[Voraussetzungen]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JP01_privacy_policy_linked_in_playstore_doc` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JQ01_concept_markers_registered` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[assistant.py]` | 0.003 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[core/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[core/interface.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[database.py]` | 0.005 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[diagnose.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[gui.py]` | 0.010 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[main.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/app.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/headless_app.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/presenters.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/export_data.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/license.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/more.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/ui_text.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[models.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/calendar.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/contracts.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/family.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/finance.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/inbox.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/overview.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/profiles.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/social.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/data_deletion.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/datadir.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/escaping.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/export.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/gemini.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/i18n.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/ical.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/import_csv.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/io_validation.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/legal.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/license_events.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/license_gate.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/license_token.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/license_ui.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/licensing.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/llm.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/logging_setup.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/notifier.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/ocr.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/open_file.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/output.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/pairing/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/pairing/identity.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/pairing/kdf.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/pairing/secure_store.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/pairing/session.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/pairing/transcript.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/payment.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/payment_adapter_lemon.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/payment_adapter_paddle.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/payment_issuer.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/payment_server.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/profile.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/reports.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/scheduler.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/sync.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/sync_runtime.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/sync_server.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/tls_certs.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/vcard.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS04_no_clear_text_attribute_default` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[assistant.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[core/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[core/interface.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[database.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[diagnose.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[gui.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[main.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/app.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/headless_app.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/presenters.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/export_data.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/license.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/more.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/ui_text.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[models.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/family.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/inbox.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/overview.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/profiles.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/social.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/data_deletion.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/datadir.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/escaping.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/export.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/gemini.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/i18n.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/ical.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/import_csv.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/io_validation.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/legal.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/license_events.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/license_gate.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/license_token.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/license_ui.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/licensing.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/llm.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/logging_setup.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/notifier.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/ocr.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/open_file.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/output.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/pairing/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/pairing/identity.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/pairing/kdf.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/pairing/secure_store.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/pairing/session.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/pairing/transcript.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/payment.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/payment_adapter_lemon.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/payment_adapter_paddle.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/payment_issuer.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/payment_server.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/profile.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/reports.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/scheduler.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/sync.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/sync_runtime.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/sync_server.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/tls_certs.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/vcard.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_concept_directory_contains_full_suite` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_dashboard_generator_module_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_md_to_html_module_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_testing_doc_contains_part_II` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_ui_concept_doc_present_and_complete` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_admin_can_invite_but_not_delete_group` | 0.000 |
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
| [pass] | `tests.concept.test_roles_permissions::test_destructive_capabilities_have_marker` | 0.800 |
| [pass] | `tests.concept.test_roles_permissions::test_guest_cannot_modify_data` | 0.000 |
| [pass] | `tests.concept.test_roles_permissions::test_license_gate_blocks_ai_in_free` | 0.853 |
| [pass] | `tests.concept.test_roles_permissions::test_license_gate_blocks_finance_writes_in_free` | 0.943 |
| [pass] | `tests.concept.test_roles_permissions::test_license_gate_passes_family_in_free` | 1.061 |
| [pass] | `tests.concept.test_roles_permissions::test_member_can_self_assign_but_not_other` | 0.000 |
| [pass] | `tests.concept.test_roles_permissions::test_owner_can_do_everything` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_owner_concept_role_maps_to_pro_license` | 0.801 |
| [pass] | `tests.test_calendar_birthday.TestBirthdayEventsDoesNotCrashOnLeapDay::test_feb_29_member_does_not_break_view` | 0.001 |
| [pass] | `tests.test_calendar_birthday.TestBirthdayInYear::test_leap_day_falls_back_to_feb_28_in_non_leap_year` | 0.001 |
| [pass] | `tests.test_calendar_birthday.TestBirthdayInYear::test_leap_day_kept_in_leap_year` | 0.001 |
| [pass] | `tests.test_calendar_birthday.TestBirthdayInYear::test_ordinary_day_unchanged` | 0.001 |
| [pass] | `tests.test_compliance_gates.TestClosedTestGate::test_checker_does_not_fail_on_missing_evidence` | 0.012 |
| [pass] | `tests.test_compliance_gates.TestClosedTestGate::test_checker_fails_on_weak_config_when_readable` | 0.001 |
| [pass] | `tests.test_compliance_gates.TestClosedTestGate::test_checker_skips_when_config_unreadable` | 0.001 |
| [pass] | `tests.test_compliance_gates.TestClosedTestGate::test_live_config_meets_minimums` | 0.012 |
| [pass] | `tests.test_compliance_gates.TestClosedTestGate::test_ready_with_config_and_evidence` | 0.002 |
| [pass] | `tests.test_compliance_gates.TestClosedTestGate::test_rejects_weak_config` | 0.002 |
| [pass] | `tests.test_compliance_gates.TestClosedTestGate::test_requires_evidence_before_go` | 0.002 |
| [pass] | `tests.test_compliance_gates.TestDataDeletionReachable::test_checker_reports_deletion_path_present` | 0.001 |
| [pass] | `tests.test_compliance_gates.TestDataDeletionReachable::test_data_deletion_reachable_from_ui` | 0.001 |
| [pass] | `tests.test_compliance_gates.TestDataDeletionReachable::test_privacy_policy_documents_inapp_deletion` | 0.001 |
| [pass] | `tests.test_data_deletion.TestDeleteAllUserData::test_end_to_end` | 0.426 |
| [pass] | `tests.test_data_deletion.TestPurgeDirectories::test_missing_dir_is_skipped` | 0.001 |
| [pass] | `tests.test_data_deletion.TestPurgeDirectories::test_removes_files_keeps_root` | 0.004 |
| [pass] | `tests.test_data_deletion.TestSandboxDataDirs::test_builds_subdir_paths` | 0.001 |
| [pass] | `tests.test_data_deletion.TestWipeAllData::test_clears_all_tables` | 0.860 |
| [pass] | `tests.test_data_deletion.TestWipeAllData::test_include_settings_false_keeps_settings` | 0.331 |
| [pass] | `tests.test_data_deletion.TestWipeAllData::test_schema_survives_wipe` | 0.299 |
| [pass] | `tests.test_data_safety.TestCheckConsistency::test_analytics_purpose_without_sdk_is_error` | 0.007 |
| [pass] | `tests.test_data_safety.TestCheckConsistency::test_clean_declaration_passes` | 0.008 |
| [pass] | `tests.test_data_safety.TestCheckConsistency::test_false_sharing_is_error` | 0.007 |
| [pass] | `tests.test_data_safety.TestCheckConsistency::test_missing_deletion_warns` | 0.003 |
| [pass] | `tests.test_data_safety.TestDataSafetyOptionalFeatures::test_email_modeled_as_optional_app_functionality` | 0.001 |
| [pass] | `tests.test_data_safety.TestDataSafetyOptionalFeatures::test_gemini_dependency_is_not_tracking` | 0.008 |
| [pass] | `tests.test_data_safety.TestDataSafetyOptionalFeatures::test_imap_dependency_is_not_tracking` | 0.008 |
| [pass] | `tests.test_data_safety.TestDataSafetyOptionalFeatures::test_user_content_not_shared_for_ads` | 0.001 |
| [pass] | `tests.test_data_safety.TestDeletionSupported::test_false_without_service` | 0.002 |
| [pass] | `tests.test_data_safety.TestDeletionSupported::test_true_when_present` | 0.007 |
| [pass] | `tests.test_data_safety.TestDetectTrackingSdks::test_detects_firebase` | 0.005 |
| [pass] | `tests.test_data_safety.TestDetectTrackingSdks::test_detects_sentry` | 0.005 |
| [pass] | `tests.test_data_safety.TestDetectTrackingSdks::test_none_for_clean_deps` | 0.010 |
| [pass] | `tests.test_data_safety.TestFormatMarkdown::test_contains_table` | 0.001 |
| [pass] | `tests.test_data_safety.TestGenerate::test_clean_app_shares_nothing` | 0.007 |
| [pass] | `tests.test_data_safety.TestGenerate::test_deletion_missing_reflected` | 0.002 |
| [pass] | `tests.test_data_safety.TestGenerate::test_tracking_dep_flips_shared` | 0.007 |
| [pass] | `tests.test_data_safety.TestRealRepo::test_real_app_has_no_tracking` | 0.001 |
| [pass] | `tests.test_data_safety.TestRealRepo::test_real_playstore_yml_is_consistent` | 0.012 |
| [pass] | `tests.test_datadir::test_activate_changes_cwd` | 0.003 |
| [pass] | `tests.test_datadir::test_blank_pointer_value_is_unconfigured` | 0.003 |
| [pass] | `tests.test_datadir::test_config_dir_honors_override` | 0.002 |
| [pass] | `tests.test_datadir::test_corrupt_pointer_is_treated_as_unconfigured` | 0.003 |
| [pass] | `tests.test_datadir::test_env_var_wins_over_pointer` | 0.003 |
| [pass] | `tests.test_datadir::test_first_run_is_unconfigured` | 0.002 |
| [pass] | `tests.test_datadir::test_migrate_into_copies_known_artifacts` | 0.015 |
| [pass] | `tests.test_datadir::test_migrate_into_noop_when_same_dir` | 0.007 |
| [pass] | `tests.test_datadir::test_migrate_into_skips_existing_targets` | 0.016 |
| [pass] | `tests.test_datadir::test_prepare_data_dir_creates_and_migrates` | 0.016 |
| [pass] | `tests.test_datadir::test_remember_and_read_roundtrip` | 0.005 |
| [pass] | `tests.test_datadir::test_remember_writes_valid_json` | 0.004 |
| [pass] | `tests.test_export_json.TestExportJson::test_export_all_json_accepts_settings_dict` | 0.939 |
| [pass] | `tests.test_export_json.TestExportJson::test_export_all_json_writes_bundle` | 0.654 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_geometry_helpers` | 0.003 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_gui_has_license_section_methods` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_gui_module_imports` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_license_ui_helpers_callable_headless` | 0.011 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_main_app_class_exists` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_only_critical_destructive_actions_need_confirmation` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_win11_theme_defaults_to_light_mode` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestMainImports::test_build_registry_signature` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestMainImports::test_main_module_imports` | 0.001 |
| [pass] | `tests.test_headless_app.TestHeadlessApp::test_all_presenters_wired` | 0.214 |
| [pass] | `tests.test_headless_app.TestHeadlessApp::test_close_is_idempotent` | 0.187 |
| [pass] | `tests.test_headless_app.TestHeadlessApp::test_end_to_end_flow_reflects_in_dashboard` | 0.196 |
| [pass] | `tests.test_headless_app.TestHeadlessApp::test_navigation_between_tabs` | 0.185 |
| [pass] | `tests.test_headless_app.TestHeadlessApp::test_unknown_tab_rejected` | 0.200 |
| [pass] | `tests.test_i18n.TestDetectDeviceLanguage::test_lang_fallback_when_no_language` | 0.003 |
| [pass] | `tests.test_i18n.TestDetectDeviceLanguage::test_priority_language_over_lang` | 0.003 |
| [pass] | `tests.test_i18n.TestDetectDeviceLanguage::test_reads_language_env` | 0.003 |
| [pass] | `tests.test_i18n.TestEuRegistry::test_24_official_languages` | 0.001 |
| [pass] | `tests.test_i18n.TestEuRegistry::test_codes_are_two_letters` | 0.001 |
| [pass] | `tests.test_i18n.TestEuRegistry::test_default_is_first` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_auto_resolves` | 0.002 |
| [pass] | `tests.test_i18n.TestI18nClass::test_available_languages_includes_default` | 0.002 |
| [pass] | `tests.test_i18n.TestI18nClass::test_default_german` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_missing_key_falls_back_to_default_lang` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_translation_lookup` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_unknown_key_returns_default_arg` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_unknown_key_returns_key` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_unknown_language_falls_back_to_default` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nSyncTool::test_all_eu_languages_have_files` | 0.002 |
| [pass] | `tests.test_i18n.TestI18nSyncTool::test_check_passes` | 0.009 |
| [pass] | `tests.test_i18n.TestI18nSyncTool::test_coverage_numbers` | 0.009 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_core_keys_present_everywhere` | 0.007 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_every_file_is_valid_json` | 0.010 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_full_languages_have_complete_parity` | 0.003 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_no_locale_has_extra_keys` | 0.007 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_placeholders_preserved_in_full_languages` | 0.005 |
| [pass] | `tests.test_i18n.TestNormalizeLanguage::test_garbage_returns_none` | 0.001 |
| [pass] | `tests.test_i18n.TestNormalizeLanguage::test_modifier_and_encoding` | 0.001 |
| [pass] | `tests.test_i18n.TestNormalizeLanguage::test_plain_code` | 0.001 |
| [pass] | `tests.test_i18n.TestNormalizeLanguage::test_region_variants` | 0.001 |
| [pass] | `tests.test_i18n.TestResolveLanguage::test_auto_unknown_device_falls_back` | 0.001 |
| [pass] | `tests.test_i18n.TestResolveLanguage::test_auto_uses_device` | 0.001 |
| [pass] | `tests.test_i18n.TestResolveLanguage::test_custom_supported_set` | 0.001 |
| [pass] | `tests.test_i18n.TestResolveLanguage::test_explicit_supported` | 0.001 |
| [pass] | `tests.test_i18n.TestResolveLanguage::test_none_falls_back` | 0.001 |
| [pass] | `tests.test_i18n.TestResolveLanguage::test_region_normalized` | 0.001 |
| [pass] | `tests.test_i18n.TestResolveLanguage::test_unsupported_falls_back_to_default` | 0.001 |
| [pass] | `tests.test_import_robustness.TestCsvImportRejectsMalformed::test_bad_number_and_date_fall_back_to_defaults` | 0.212 |
| [pass] | `tests.test_import_robustness.TestCsvImportRejectsMalformed::test_calendar_skips_rows_without_title_or_date` | 0.193 |
| [pass] | `tests.test_import_robustness.TestCsvImportRejectsMalformed::test_contracts_skips_rows_without_name` | 0.155 |
| [pass] | `tests.test_import_robustness.TestCsvImportRejectsMalformed::test_expenses_skips_rows_without_description` | 0.162 |
| [pass] | `tests.test_import_robustness.TestCsvImportRejectsMalformed::test_family_skips_rows_without_name` | 0.168 |
| [pass] | `tests.test_import_robustness.TestCsvImportRejectsMalformed::test_social_skips_rows_without_name` | 0.184 |
| [pass] | `tests.test_import_robustness.TestIcsImportDstRecurrence::test_floating_time_on_dst_day_keeps_calendar_date` | 0.002 |
| [pass] | `tests.test_import_robustness.TestIcsImportDstRecurrence::test_pure_date_yearly_recurrence_preserved` | 0.002 |
| [pass] | `tests.test_import_robustness.TestIcsImportDstRecurrence::test_tzid_parameter_is_stripped_date_stable` | 0.002 |
| [pass] | `tests.test_integration.TestHttpsSyncServer::test_tls_handshake_with_self_signed_cert` | 0.691 |
| [pass] | `tests.test_integration.TestImapAbruf::test_fetch_imap_loops_through_unseen` | 0.176 |
| [pass] | `tests.test_integration.TestOcrParsing::test_missing_engine_returns_hint` | 0.003 |
| [pass] | `tests.test_integration.TestOcrParsing::test_receipt_text_extraction` | 0.002 |
| [pass] | `tests.test_integration.TestPrinten::test_print_file_calls_lpr_on_macos` | 0.002 |
| [pass] | `tests.test_integration.TestPrinten::test_print_file_calls_subprocess_on_unix` | 0.002 |
| [pass] | `tests.test_integration.TestPrinten::test_print_file_missing_returns_error` | 0.001 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_calls_protocol` | 0.008 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_handles_server_error` | 0.003 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_skips_starttls_when_disabled` | 0.003 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_without_config_returns_skip` | 0.001 |
| [pass] | `tests.test_legal.TestRealRepoFallback::test_all_docs_resolve_to_german` | 0.001 |
| [pass] | `tests.test_legal.TestRealRepoFallback::test_coverage_lists_german` | 0.002 |
| [pass] | `tests.test_legal.TestRealRepoFallback::test_legal_path_points_at_existing_file` | 0.001 |
| [pass] | `tests.test_legal.TestRealRepoFallback::test_unknown_language_falls_back_to_german` | 0.001 |
| [pass] | `tests.test_legal.TestTranslationResolution::test_missing_doc_returns_none` | 0.001 |
| [pass] | `tests.test_legal.TestTranslationResolution::test_prefers_translation_when_present` | 0.004 |
| [pass] | `tests.test_legal.TestTranslationResolution::test_translation_dir_without_doc_falls_back` | 0.003 |
| [pass] | `tests.test_mobile_helpers.TestBuildOrderPayload::test_full_payload` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestBuildOrderPayload::test_optional_fields_omitted_and_priority_defaulted` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestBuildOrderPayload::test_requires_title` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestBuildSearchArgs::test_filters_included_when_set` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestBuildSearchArgs::test_query_only` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestBuildSearchArgs::test_validity_filter_only` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestBuildSearchArgs::test_validity_query_min_length` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDashboardSummary::test_aggregates_three_sources` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDashboardSummary::test_robust_against_errors` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDashboardSummary::test_truncates_to_phone_friendly_count` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDaysUntil::test_future` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDaysUntil::test_invalid` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDaysUntil::test_past` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDaysUntil::test_today` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestDistinctValues::test_sorted_unique_nonempty` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_invalid` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_normal` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_other_currency` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_thousands_separator` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestFormatCurrency::test_zero` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestGroupByModule::test_groups_by_module_id` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestGroupByModule::test_unknown_falls_back` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_auto_selected` | 0.002 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_contains_all_available_languages` | 0.003 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_default_selects_english` | 0.002 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_exactly_one_selected` | 0.007 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_first_entry_is_auto` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_region_code_normalized` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_unknown_setting_falls_back_to_default` | 0.002 |
| [pass] | `tests.test_mobile_helpers.TestNormalizePriority::test_invalid_falls_back_to_normal` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestNormalizePriority::test_valid_values` | 0.001 |
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
| [pass] | `tests.test_mobile_helpers.TestWeekAgenda::test_custom_horizon_forwarded` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestWeekAgenda::test_passes_through_days_and_overdue` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestWeekAgenda::test_robust_against_errors` | 0.001 |
| [pass] | `tests.test_mobile_screen_capabilities.TestMobileScreenCapabilities::test_all_referenced_capabilities_exist` | 0.182 |
| [pass] | `tests.test_notifications_permission.TestNotifierGracefulDegradation::test_notify_does_not_raise_without_permission` | 0.002 |
| [pass] | `tests.test_notifications_permission.TestPostNotificationsPermission::test_manifest_declares_post_notifications` | 0.001 |
| [pass] | `tests.test_notifications_permission.TestPostNotificationsPermission::test_no_denied_sensitive_permission_in_manifest` | 0.001 |
| [pass] | `tests.test_notifications_permission.TestPostNotificationsPermission::test_only_whitelisted_permissions_declared` | 0.001 |
| [pass] | `tests.test_notifications_permission.TestPostNotificationsPermission::test_playstore_yml_declares_post_notifications` | 0.019 |
| [pass] | `tests.test_overview.TestAgendaOverview::test_day_view_groups_due_items` | 0.205 |
| [pass] | `tests.test_overview.TestAgendaOverview::test_events_outside_horizon_excluded_then_included` | 0.164 |
| [pass] | `tests.test_overview.TestAgendaOverview::test_invalid_horizon_rejected` | 0.226 |
| [pass] | `tests.test_overview.TestAgendaOverview::test_total_matches_buckets` | 0.160 |
| [pass] | `tests.test_overview.TestAgendaOverview::test_week_view_spans_seven_days` | 0.154 |
| [pass] | `tests.test_overview.TestAgendaOverview::test_weekday_label_matches_date` | 0.156 |
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
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_delete_removes_from_list` | 0.023 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_list_keys_returns_set_keys` | 0.044 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_manifest_key_is_reserved` | 0.002 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_roundtrip` | 0.020 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_default_length_32` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_deterministic` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_distinct_inputs_distinct_outputs` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_rejects_bad_length` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_calls_in_wrong_order_raise` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_initiator_cannot_make_proof_before_learning_responder_key` | 0.021 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_rejects_bad_signature_length` | 0.021 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_responder_with_wrong_initiator_pubkey_in_invitation` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_wrong_ot_secret_breaks_handshake` | 0.021 |
| [pass] | `tests.test_pairing_handshake.TestPairingHappyPath::test_both_sides_derive_same_psk` | 0.022 |
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
| [pass] | `tests.test_performance.TestBulkInsertPerformance::test_insert_500_contracts_under_15s` | 2.914 |
| [pass] | `tests.test_performance.TestBulkInsertPerformance::test_insert_500_expenses_under_15s` | 2.783 |
| [pass] | `tests.test_performance.TestBulkInsertPerformance::test_list_200_contracts_under_2s` | 1.143 |
| [pass] | `tests.test_performance.TestDeadlineCalculationPerformance::test_deadline_calculation_scales` | 0.144 |
| [pass] | `tests.test_performance.TestNotesListingPerformance::test_list_attached_in_large_dataset` | 5.623 |
| [pass] | `tests.test_persistence_robustness.TestCalendarRecurrenceGuard::test_negative_recurrence_does_not_hang` | 0.001 |
| [pass] | `tests.test_persistence_robustness.TestCalendarRecurrenceGuard::test_positive_recurrence_still_advances` | 0.001 |
| [pass] | `tests.test_persistence_robustness.TestCalendarRecurrenceGuard::test_zero_recurrence_is_safe` | 0.001 |
| [pass] | `tests.test_persistence_robustness.TestOrphanOwnerId::test_contract_with_unknown_owner_stores_null` | 0.160 |
| [pass] | `tests.test_persistence_robustness.TestOrphanOwnerId::test_contract_with_valid_owner_is_kept` | 0.162 |
| [pass] | `tests.test_persistence_robustness.TestOrphanOwnerId::test_expense_with_unknown_owner_stores_null` | 0.173 |
| [pass] | `tests.test_persistence_robustness.TestOrphanOwnerId::test_set_owner_with_unknown_id_clears_it` | 0.183 |
| [pass] | `tests.test_persistence_robustness.TestProposalCreatedAt::test_created_at_is_loaded_as_datetime` | 0.147 |
| [pass] | `tests.test_persistence_robustness.TestSoftDeletedOwnerName::test_soft_deleted_owner_name_is_hidden` | 0.214 |
| [pass] | `tests.test_playstore_check.TestCheckDataDeletion::test_fails_when_service_missing` | 0.005 |
| [pass] | `tests.test_playstore_check.TestCheckDataDeletion::test_fails_when_wipe_method_missing` | 0.008 |
| [pass] | `tests.test_playstore_check.TestCheckDataDeletion::test_passes_when_mechanism_present` | 0.006 |
| [pass] | `tests.test_playstore_check.TestCheckDemoData::test_fails_when_db_missing` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckDemoData::test_passes_when_db_and_sqlite_excluded` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckI18n::test_real_repo_parity_passes` | 0.009 |
| [pass] | `tests.test_playstore_check.TestCheckPermissions::test_denied_permission_fails` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckPermissions::test_empty_permissions_passes` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckPermissions::test_unknown_permission_warns` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckPermissions::test_whitelisted_passes` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckSdkLevels::test_fails_below_min_target` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckSdkLevels::test_flags_too_low_minapi` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckSdkLevels::test_passes_at_or_above_target` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckSecrets::test_clean_repo_passes` | 0.007 |
| [pass] | `tests.test_playstore_check.TestCheckSecrets::test_detects_google_api_key` | 0.006 |
| [pass] | `tests.test_playstore_check.TestCheckVersioning::test_invalid_warns` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckVersioning::test_missing_fails` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckVersioning::test_semver_passes` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCodeSmells::test_print_only_in_mobile_path` | 0.004 |
| [pass] | `tests.test_playstore_check.TestCodeSmells::test_requests_verify_false_is_smell` | 0.006 |
| [pass] | `tests.test_playstore_check.TestParseBuildozerSpec::test_extracts_app_block` | 0.002 |
| [pass] | `tests.test_playstore_check.TestParseBuildozerSpec::test_handles_missing_file` | 0.001 |
| [pass] | `tests.test_playstore_check.TestParseBuildozerSpec::test_ignores_comments_and_blanks` | 0.002 |
| [pass] | `tests.test_playstore_check.TestReportFormats::test_json_format_valid` | 0.001 |
| [pass] | `tests.test_playstore_check.TestReportFormats::test_summary_counts` | 0.001 |
| [pass] | `tests.test_playstore_check.TestRunChecksIntegration::test_runs_without_exception` | 0.197 |
| [pass] | `tests.test_playstore_check.TestRunChecksIntegration::test_subset_only` | 0.005 |
| [pass] | `tests.test_presenters.TestPresenters::test_calendar_add_and_list` | 0.217 |
| [pass] | `tests.test_presenters.TestPresenters::test_calendar_add_via_presenter_defaults_title` | 0.183 |
| [pass] | `tests.test_presenters.TestPresenters::test_contacts_relation_filter_and_options` | 0.219 |
| [pass] | `tests.test_presenters.TestPresenters::test_contracts_add_list_filter_detail_delete` | 0.200 |
| [pass] | `tests.test_presenters.TestPresenters::test_contracts_empty_state` | 0.177 |
| [pass] | `tests.test_presenters.TestPresenters::test_dashboard_summary_and_week` | 0.202 |
| [pass] | `tests.test_presenters.TestPresenters::test_finance_add_and_recent_total` | 0.174 |
| [pass] | `tests.test_presenters.TestPresenters::test_finance_add_rejects_bad_amount` | 0.175 |
| [pass] | `tests.test_presenters.TestPresenters::test_finance_list_empty_then_filled` | 0.195 |
| [pass] | `tests.test_presenters.TestPresenters::test_interpolated_empty_views_expose_key_and_params` | 0.175 |
| [pass] | `tests.test_presenters.TestPresenters::test_list_views_expose_i18n_keys` | 0.214 |
| [pass] | `tests.test_presenters.TestPresenters::test_orders_add_priority_category_and_complete` | 0.206 |
| [pass] | `tests.test_presenters.TestPresenters::test_orders_invalid_priority_defaults_normal` | 0.186 |
| [pass] | `tests.test_presenters.TestPresenters::test_orders_requires_title` | 0.153 |
| [pass] | `tests.test_presenters.TestPresenters::test_search_filter_only_without_query` | 0.155 |
| [pass] | `tests.test_presenters.TestPresenters::test_search_hits_and_empty` | 0.157 |
| [pass] | `tests.test_presenters.TestPresenters::test_search_states_expose_message_keys` | 0.169 |
| [pass] | `tests.test_presenters.TestPresenters::test_search_too_short` | 0.158 |
| [pass] | `tests.test_priority_category.TestOrderSchemaMigration::test_migration_adds_columns_and_keeps_rows` | 0.115 |
| [pass] | `tests.test_priority_category.TestPriorityAndCategoryFilters::test_add_order_rejects_invalid_priority` | 0.168 |
| [pass] | `tests.test_priority_category.TestPriorityAndCategoryFilters::test_contacts_filter_by_relation` | 0.182 |
| [pass] | `tests.test_priority_category.TestPriorityAndCategoryFilters::test_contracts_filter_by_category` | 0.179 |
| [pass] | `tests.test_priority_category.TestPriorityAndCategoryFilters::test_order_default_priority_is_normal` | 0.179 |
| [pass] | `tests.test_priority_category.TestPriorityAndCategoryFilters::test_order_priority_sort_order` | 0.192 |
| [pass] | `tests.test_priority_category.TestPriorityAndCategoryFilters::test_orders_filter_by_category` | 0.157 |
| [pass] | `tests.test_privacy_policy.TestBuildHtml::test_renders_markdown` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestBuildHtml::test_self_contained_document` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestCheck::test_finalized_policy_no_warning_about_placeholders` | 0.018 |
| [pass] | `tests.test_privacy_policy.TestCheck::test_missing_file_is_error` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestCheck::test_placeholders_warn` | 0.017 |
| [pass] | `tests.test_privacy_policy.TestFindPlaceholders::test_clean_text_returns_empty` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestFindPlaceholders::test_detects_template_tokens` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestFindPlaceholders::test_ignores_markdown_links` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestFindPlaceholders::test_unique_and_sorted` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestRealRepo::test_real_build_produces_article` | 0.002 |
| [pass] | `tests.test_privacy_policy.TestRealRepo::test_real_check_has_no_errors` | 0.012 |
| [pass] | `tests.test_profiles.TestProfilesManager::test_create_appears_and_becomes_active` | 0.004 |
| [pass] | `tests.test_profiles.TestProfilesManager::test_default_is_active_initially` | 0.001 |
| [pass] | `tests.test_profiles.TestProfilesManager::test_env_var_overrides_pointer` | 0.002 |
| [pass] | `tests.test_profiles.TestProfilesManager::test_invalid_name_rejected` | 0.001 |
| [pass] | `tests.test_profiles.TestProfilesManager::test_name_is_sanitized` | 0.003 |
| [pass] | `tests.test_profiles.TestProfilesManager::test_switch_changes_active_and_persists` | 0.029 |
| [pass] | `tests.test_profiles.TestProfilesManager::test_switch_to_default` | 0.004 |
| [pass] | `tests.test_profiles.TestProfilesModule::test_capabilities_use_system_prefix` | 0.001 |
| [pass] | `tests.test_profiles.TestProfilesModule::test_create_invalid_returns_error` | 0.001 |
| [pass] | `tests.test_profiles.TestProfilesModule::test_list_create_switch_flow` | 0.006 |
| [pass] | `tests.test_requirements_coverage.TestRequirementsCoverage::test_every_requirement_has_at_least_one_test` | 0.001 |
| [pass] | `tests.test_requirements_coverage.TestRequirementsCoverage::test_mapped_files_exist_and_contain_tests` | 0.124 |
| [pass] | `tests.test_requirements_coverage.TestRequirementsCoverage::test_mapping_uses_only_known_requirements` | 0.001 |
| [pass] | `tests.test_requirements_coverage.TestRequirementsCoverage::test_requirement_catalog_is_complete` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderPersistence::test_clock_change_does_not_resend` | 0.005 |
| [pass] | `tests.test_scheduler_reminders.TestReminderPersistence::test_corrupt_state_file_is_ignored` | 0.004 |
| [pass] | `tests.test_scheduler_reminders.TestReminderPersistence::test_new_event_after_restart_still_fires` | 0.006 |
| [pass] | `tests.test_scheduler_reminders.TestReminderPersistence::test_seen_markers_survive_restart` | 0.004 |
| [pass] | `tests.test_scheduler_reminders.TestReminderPersistence::test_without_state_path_refires_after_restart` | 0.003 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_future_event_phrasing` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_multiple_due_events_all_trigger` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_new_event_after_first_check_still_fires` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_overdue_event_phrasing` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_reminder_not_repeated_on_recheck` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_today_event_phrasing` | 0.001 |
| [pass] | `tests.test_search_filters.TestSearchFilters::test_search_combines_query_and_filter` | 0.202 |
| [pass] | `tests.test_search_filters.TestSearchFilters::test_search_empty_query_with_filter_lists_filtered` | 0.189 |
| [pass] | `tests.test_search_filters.TestSearchFilters::test_search_filters_by_category` | 0.209 |
| [pass] | `tests.test_search_filters.TestSearchFilters::test_search_filters_by_date_range` | 0.201 |
| [pass] | `tests.test_search_filters.TestSearchFilters::test_search_filters_by_status` | 0.206 |
| [pass] | `tests.test_search_filters.TestSearchFilters::test_search_invalid_date_rejected` | 0.220 |
| [pass] | `tests.test_search_filters.TestSearchFilters::test_search_short_query_without_filter_rejected` | 0.243 |
| [pass] | `tests.test_smoke.TestAssistantLogRotation::test_log_does_not_grow_unbounded` | 0.319 |
| [pass] | `tests.test_smoke.TestAutoBackup::test_prune_old_backups_keeps_newest` | 0.205 |
| [pass] | `tests.test_smoke.TestAutoBackup::test_run_once_creates_backup_and_prunes` | 0.293 |
| [pass] | `tests.test_smoke.TestBackupAndRestore::test_list_backups_sorted_newest_first` | 0.229 |
| [pass] | `tests.test_smoke.TestBackupAndRestore::test_online_backup_creates_readable_copy` | 0.174 |
| [pass] | `tests.test_smoke.TestBackupAndRestore::test_restore_overwrites_live_db` | 0.204 |
| [pass] | `tests.test_smoke.TestBackupSqlCipherPath::test_sqlcipher_path_rejects_short_key` | 0.002 |
| [pass] | `tests.test_smoke.TestBackupSqlCipherPath::test_sqlcipher_path_requires_key` | 0.001 |
| [pass] | `tests.test_smoke.TestBulkOperations::test_bulk_complete_overdue_tasks` | 0.217 |
| [pass] | `tests.test_smoke.TestBulkOperations::test_bulk_delete_archived` | 0.188 |
| [pass] | `tests.test_smoke.TestBulkOperations::test_bulk_reject_open_proposals` | 0.165 |
| [pass] | `tests.test_smoke.TestCalendarNoMutation::test_recurring_event_not_mutated_in_db` | 0.172 |
| [pass] | `tests.test_smoke.TestCompleteTaskCatchUp::test_overdue_task_advances_rotation_multiple_times` | 0.203 |
| [pass] | `tests.test_smoke.TestConversationHistory::test_history_grows_across_calls` | 0.169 |
| [pass] | `tests.test_smoke.TestCsvExport::test_export_all_writes_five_files` | 0.226 |
| [pass] | `tests.test_smoke.TestCsvExport::test_export_contracts_writes_csv` | 0.193 |
| [pass] | `tests.test_smoke.TestCsvImportRoundTrip::test_export_then_import_reproduces_data` | 0.454 |
| [pass] | `tests.test_smoke.TestCsvImportRoundTrip::test_invalid_dates_dont_crash` | 0.186 |
| [pass] | `tests.test_smoke.TestCsvImportRoundTrip::test_missing_csv_files_are_skipped` | 0.201 |
| [pass] | `tests.test_smoke.TestDayStructurePersistence::test_entry_persists` | 0.176 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_caps_are_destructive` | 0.189 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_contract_round_trip` | 0.174 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_member_keeps_orphan_contracts` | 0.175 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_unknown_returns_error` | 0.163 |
| [pass] | `tests.test_smoke.TestDestructiveFlags::test_critical_capabilities_are_marked` | 0.171 |
| [pass] | `tests.test_smoke.TestDiagnose::test_collect_returns_expected_shape` | 1.079 |
| [pass] | `tests.test_smoke.TestDisabledModuleSurfaced::test_disabled_contracts_yields_warning_in_finance_events` | 0.155 |
| [pass] | `tests.test_smoke.TestEncryption::test_encryption_requires_sqlcipher3` | 0.003 |
| [pass] | `tests.test_smoke.TestEncryption::test_plain_mode_when_no_key` | 0.186 |
| [pass] | `tests.test_smoke.TestGeminiAssistantStub::test_mode_reports_llm` | 0.274 |
| [pass] | `tests.test_smoke.TestGeminiAssistantStub::test_token_usage_accumulates` | 0.218 |
| [pass] | `tests.test_smoke.TestHasCapabilityHonorsDisabled::test_has_capability_false_when_disabled` | 0.149 |
| [pass] | `tests.test_smoke.TestHasCapabilityHonorsDisabled::test_has_capability_returns_after_enable` | 0.158 |
| [pass] | `tests.test_smoke.TestHttpSyncRoundTrip::test_http_provider_append_and_fetch` | 0.518 |
| [pass] | `tests.test_smoke.TestI18n::test_default_german` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_en_missing_key_falls_back_to_de` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_english_translation` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_missing_key_returns_key` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_missing_key_with_default` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_unknown_language_falls_back_to_default` | 0.001 |
| [pass] | `tests.test_smoke.TestIcalExport::test_export_creates_valid_ical` | 0.167 |
| [pass] | `tests.test_smoke.TestIcalImportRoundTrip::test_import_missing_file_returns_error` | 0.149 |
| [pass] | `tests.test_smoke.TestIcalImportRoundTrip::test_roundtrip` | 0.333 |
| [pass] | `tests.test_smoke.TestInboxExtractText::test_empty_payload_returns_empty_string` | 0.001 |
| [pass] | `tests.test_smoke.TestInboxExtractText::test_multipart_without_textplain_returns_empty` | 0.001 |
| [pass] | `tests.test_smoke.TestInputValidation::test_calendar_unknown_category_normalizes` | 0.176 |
| [pass] | `tests.test_smoke.TestInputValidation::test_family_task_rejects_zero_interval` | 0.187 |
| [pass] | `tests.test_smoke.TestInputValidation::test_finance_rejects_bad_date` | 0.168 |
| [pass] | `tests.test_smoke.TestInputValidation::test_finance_rejects_negative_amount` | 0.172 |
| [pass] | `tests.test_smoke.TestInputValidation::test_social_rejects_empty_name` | 0.267 |
| [pass] | `tests.test_smoke.TestInputValidation::test_social_rejects_non_positive_cadence` | 0.269 |
| [pass] | `tests.test_smoke.TestLamportCrdt::test_clock_ticks_monotonically` | 0.001 |
| [pass] | `tests.test_smoke.TestLamportCrdt::test_events_get_lamport_counter` | 0.184 |
| [pass] | `tests.test_smoke.TestLamportCrdt::test_replay_order_uses_lamport` | 0.003 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_apply_token_rejects_empty` | 0.153 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_apply_token_rejects_garbage` | 0.173 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_apply_token_round_trip` | 0.192 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_start_trial_success_then_blocked` | 0.188 |
| [pass] | `tests.test_smoke.TestLicensing::test_activate_pro_requires_signed_token_by_default` | 0.209 |
| [pass] | `tests.test_smoke.TestLicensing::test_activation_rejects_free_tier` | 0.182 |
| [pass] | `tests.test_smoke.TestLicensing::test_activation_requires_withdrawal_waiver` | 0.185 |
| [pass] | `tests.test_smoke.TestLicensing::test_affiliate_block_empty_when_no_partners` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_affiliate_block_format` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_affiliate_block_in_letter_text_is_static` | 0.170 |
| [pass] | `tests.test_smoke.TestLicensing::test_all_quotes_returns_pricing_tiers` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_annual_applies_20_percent_discount` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_annual_savings_vs_monthly` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_annual_total_matches_readme_base_tier` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_apply_token_persists_token_string` | 0.176 |
| [pass] | `tests.test_smoke.TestLicensing::test_build_pricing_rows_marks_recommended` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_build_pricing_rows_skips_family_above_cap` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_cancellation_includes_affiliate_suggestions` | 0.201 |
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
| [pass] | `tests.test_smoke.TestLicensing::test_grandfathered_keeps_read_but_blocks_write` | 0.198 |
| [pass] | `tests.test_smoke.TestLicensing::test_grandfathering_migration_runs_once` | 0.197 |
| [pass] | `tests.test_smoke.TestLicensing::test_grandfathering_skipped_for_empty_db` | 0.178 |
| [pass] | `tests.test_smoke.TestLicensing::test_invalid_persons_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_issuer_signs_token_and_sends_mail` | 0.009 |
| [pass] | `tests.test_smoke.TestLicensing::test_issuer_skips_cancellations` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_lemon_signature_and_parse` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_lemon_uninteresting_event_returns_none` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_defaults_to_free` | 0.236 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_drops_tampered_token` | 0.232 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_handles_corrupt_values` | 0.205 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_keeps_expired_token_for_grace` | 0.185 |
| [pass] | `tests.test_smoke.TestLicensing::test_mobile_pricing_has_markup` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_monthly_base_two_persons` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_monthly_charges_extra_persons` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_paddle_parse_event` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_paddle_signature_round_trip` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_paddle_unknown_price_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_pricing_onboarded_flag_persists` | 0.150 |
| [pass] | `tests.test_smoke.TestLicensing::test_pro_downgrades_after_grace_period` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_pro_license_unlocks_everything` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_recommended_tier_picks_family_above_break_even` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_registry_pre_dispatch_hook_blocks_calls` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_event_for_pro_near_expiry` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_event_for_trial_near_end` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_event_in_grace_period` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_event_outside_warning_window` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_renewal_no_event_for_free` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_revocation_supersedes_grace_period` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_revoked_token_is_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_scheduler_picks_up_extra_event_sources` | 0.001 |
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
| [pass] | `tests.test_smoke.TestLicensing::test_token_rejects_expired` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_rejects_tampered_payload` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_sign_verify_round_trip` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_without_configured_pubkey_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_trial_is_not_reusable` | 0.184 |
| [pass] | `tests.test_smoke.TestLicensing::test_trial_starts_and_expires` | 0.208 |
| [pass] | `tests.test_smoke.TestLicensing::test_unsigned_pro_settings_downgrade_to_free` | 0.172 |
| [pass] | `tests.test_smoke.TestLicensing::test_webhook_server_end_to_end` | 0.517 |
| [pass] | `tests.test_smoke.TestLicensing::test_webhook_server_rejects_bad_signature` | 0.514 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_fenced_json` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_fenced_without_lang` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_invalid_returns_empty` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_plain_json` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_prose_with_embedded_json` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmProposalValidation::test_missing_required_dropped` | 0.187 |
| [pass] | `tests.test_smoke.TestLlmProposalValidation::test_unknown_target_capability_dropped` | 0.146 |
| [pass] | `tests.test_smoke.TestModuleStatePersistence::test_disabled_module_id_persists` | 0.191 |
| [pass] | `tests.test_smoke.TestNotesModule::test_add_list_update_attach_delete` | 0.198 |
| [pass] | `tests.test_smoke.TestNotesModule::test_empty_title_rejected` | 0.157 |
| [pass] | `tests.test_smoke.TestNotesModule::test_invalid_entity_type_rejected` | 0.137 |
| [pass] | `tests.test_smoke.TestNotesModule::test_search_finds_notes` | 0.150 |
| [pass] | `tests.test_smoke.TestPrintFileNoShell::test_missing_file_returns_error` | 0.001 |
| [pass] | `tests.test_smoke.TestPrintFileNoShell::test_path_with_spaces_handled` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_db_path_default` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_db_path_with_profile` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_explicit_overrides_env` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_resolve_profile_uses_env` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_sanitize_profile` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_state_dir_default_and_profile` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_two_profiles_use_separate_files` | 0.283 |
| [pass] | `tests.test_smoke.TestProposalUpdate::test_update_blocked_after_accept` | 0.229 |
| [pass] | `tests.test_smoke.TestProposalUpdate::test_update_payload_replaces_value` | 0.220 |
| [pass] | `tests.test_smoke.TestProposalUpdate::test_update_then_accept_uses_new_payload` | 0.201 |
| [pass] | `tests.test_smoke.TestProposalsFlow::test_price_change_round_trip` | 0.162 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_invalid_date_rejected` | 0.181 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_negative_recurrence_rejected` | 0.206 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_none_recurrence_ok` | 0.158 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_positive_recurrence_ok` | 0.176 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_zero_recurrence_rejected` | 0.162 |
| [pass] | `tests.test_smoke.TestRegistry::test_capabilities_registered` | 0.142 |
| [pass] | `tests.test_smoke.TestRegistry::test_module_to_module_via_context` | 0.171 |
| [pass] | `tests.test_smoke.TestRegistry::test_unknown_capability_returns_error` | 0.183 |
| [pass] | `tests.test_smoke.TestRegistryGetCapability::test_returns_capability_object` | 0.174 |
| [pass] | `tests.test_smoke.TestRegistryGetCapability::test_returns_none_for_disabled_module` | 0.175 |
| [pass] | `tests.test_smoke.TestRegistryGetCapability::test_returns_none_for_unknown` | 0.202 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_assistant_ask_lock_serializes` | 0.148 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_bulk_complete_overdue_dispatches_individual_tasks` | 0.170 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_bulk_delete_archived_uses_repository_method` | 0.189 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_deleting_contract_cleans_attached_notes` | 0.183 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_geometry_validation` | 0.163 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_http_provider_has_read_all` | 4.247 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_export_folds_at_byte_boundary` | 0.179 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_import_rejects_nonexistent` | 0.143 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_import_rejects_path_outside_or_bad_extension` | 0.168 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_import_validates_recurrence` | 0.160 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_initial_lamport_ignores_other_devices` | 0.158 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_internal_capabilities_hidden_from_llm` | 0.188 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_notes_entity_id_zero_preserved` | 0.187 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_rrule_uses_yearly_for_365` | 0.178 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_sync_event_args_deep_copy` | 0.189 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_unescape_preserves_real_null_bytes` | 0.200 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_vcard_import_clamps_cadence` | 0.189 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_vcard_import_rejects_too_large` | 0.152 |
| [pass] | `tests.test_smoke.TestSearch::test_no_hit` | 0.199 |
| [pass] | `tests.test_smoke.TestSearch::test_search_finds_multiple_sources` | 0.265 |
| [pass] | `tests.test_smoke.TestSearch::test_short_query_rejected` | 0.157 |
| [pass] | `tests.test_smoke.TestSettings::test_db_value_overrides_default` | 0.150 |
| [pass] | `tests.test_smoke.TestSettings::test_defaults_when_empty` | 0.177 |
| [pass] | `tests.test_smoke.TestSettings::test_env_overrides_db` | 0.168 |
| [pass] | `tests.test_smoke.TestSettings::test_secret_is_not_persisted` | 0.186 |
| [pass] | `tests.test_smoke.TestSmtpWiring::test_smtp_config_from_app_config` | 0.001 |
| [pass] | `tests.test_smoke.TestSqlCipherValidation::test_nul_byte_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestSqlCipherValidation::test_too_short_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestStatistics::test_contracts_overview_top_3` | 0.218 |
| [pass] | `tests.test_smoke.TestStatistics::test_expenses_per_category_aggregates` | 0.216 |
| [pass] | `tests.test_smoke.TestStatistics::test_expenses_per_month_returns_buckets` | 0.231 |
| [pass] | `tests.test_smoke.TestStatistics::test_rejects_zero_months` | 0.202 |
| [pass] | `tests.test_smoke.TestStatistics::test_yearly_summary` | 0.201 |
| [pass] | `tests.test_smoke.TestSyncCompaction::test_compact_drops_oldest` | 0.027 |
| [pass] | `tests.test_smoke.TestSyncExpandedCapabilities::test_contract_replays_on_other_device` | 0.395 |
| [pass] | `tests.test_smoke.TestSyncReentry::test_non_synced_outer_lets_nested_log` | 0.194 |
| [pass] | `tests.test_smoke.TestSyncReentry::test_synced_outer_suppresses_synced_nested` | 0.184 |
| [pass] | `tests.test_smoke.TestSyncServerCompaction::test_server_drops_oldest_when_over_limit` | 0.579 |
| [pass] | `tests.test_smoke.TestSyncServerTls::test_serve_with_bad_cert_path_raises` | 0.003 |
| [pass] | `tests.test_smoke.TestThreadSafety::test_concurrent_dispatch` | 0.658 |
| [pass] | `tests.test_smoke.TestUtcTimestamps::test_event_timestamp_has_utc_marker` | 0.181 |
| [pass] | `tests.test_smoke.TestUtcTimestampsInDb::test_assistant_log_uses_utc` | 0.178 |
| [pass] | `tests.test_smoke.TestUtcTimestampsInDb::test_contract_created_at_uses_utc` | 0.155 |
| [pass] | `tests.test_smoke.TestVCardExport::test_export_creates_valid_vcard` | 0.176 |
| [pass] | `tests.test_smoke.TestVCardImportRoundTrip::test_roundtrip_preserves_rhythmus` | 0.329 |
| [pass] | `tests.test_smoke.TestYearlyPdfReport::test_pdf_report_produced` | 0.210 |
| [pass] | `tests.test_store_listing.TestCuratedQuality::test_all_curated_within_limits` | 0.001 |
| [pass] | `tests.test_store_listing.TestGenerateLocalizations::test_does_not_overwrite_existing` | 0.001 |
| [pass] | `tests.test_store_listing.TestGenerateLocalizations::test_generated_is_valid` | 0.001 |
| [pass] | `tests.test_store_listing.TestGenerateLocalizations::test_merges_curated_into_base` | 0.001 |
| [pass] | `tests.test_store_listing.TestRealRepo::test_real_has_major_languages` | 0.019 |
| [pass] | `tests.test_store_listing.TestRealRepo::test_real_localizations_valid` | 0.012 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_clean_curated_passes` | 0.001 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_empty_is_error` | 0.001 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_limits_match_play` | 0.001 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_missing_field_is_error` | 0.001 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_too_long_title_is_error` | 0.001 |
| [pass] | `tests.test_sync_conflict.TestSyncConflictDeterminism::test_concurrent_edit_same_record_resolves_deterministically` | 0.409 |
| [pass] | `tests.test_sync_conflict.TestSyncConflictDeterminism::test_unseen_events_tiebreak_is_order_independent` | 0.010 |
| [pass] | `tests.test_sync_reliability.TestSyncReliability::test_failed_remote_event_is_not_marked_seen` | 0.001 |
| [pass] | `tests.test_sync_reliability.TestSyncReliability::test_local_append_failure_is_reported` | 0.001 |
| [pass] | `tests.test_sync_reliability.TestSyncReliability::test_successful_remote_event_is_marked_seen` | 0.001 |
| [pass] | `tests.test_sync_runtime.TestSyncRuntime::test_free_license_blocks_sync` | 0.198 |
| [pass] | `tests.test_sync_runtime.TestSyncRuntime::test_pro_license_allows_sync_when_configured` | 0.238 |
| [pass] | `tests.test_sync_runtime.TestSyncRuntime::test_sync_disabled_via_config` | 0.171 |
| [pass] | `tests.test_sync_runtime.TestSyncRuntime::test_ui_enable_sync_uses_license_not_stale_config` | 0.181 |
| [pass] | `tests.test_sync_threadsafety.TestSyncReplayThreadSafety::test_concurrent_user_edit_during_replay_is_logged` | 0.173 |
| [pass] | `tests.test_tls_certs.TestSelfSignedCert::test_does_not_overwrite_without_flag` | 0.118 |
| [pass] | `tests.test_tls_certs.TestSelfSignedCert::test_generates_valid_cert_and_key` | 0.104 |
| [pass] | `tests.test_tls_certs.TestSelfSignedCert::test_loads_into_ssl_context` | 0.065 |
| [pass] | `tests.test_ui_text.TestUiText::test_falls_back_to_key_without_default` | 0.001 |
| [pass] | `tests.test_ui_text.TestUiText::test_returns_default_without_running_app` | 0.001 |
| [pass] | `tests.test_ui_text.TestUiText::test_uses_running_app_i18n_when_present` | 0.001 |
| [skip] | `tests.test_gui_boot_smoke.TestGuiBootSmoke::test_app_boots_builds_and_refreshes` | 0.001 |
| [skip] | `tests.test_integration.TestGeminiRealApi::test_simple_ask_returns_text` | 0.001 |
| [skip] | `tests.test_integration.TestSqlCipherRealRoundTrip::test_encrypt_write_close_reopen` | 0.002 |
| [skip] | `tests.test_mobile_boot_smoke.TestMobileBootSmoke::test_app_boots_and_builds_all_tabs` | 0.001 |
| [skip] | `tests.test_property.TestPropertyBasedSkipped::test_skipped` | 0.001 |
| [skip] | `tests.test_tls_certs.TestSelfSignedCert::test_key_permissions_restrictive_on_posix` | 0.001 |

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

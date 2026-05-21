# Test-Protokoll

- Datum: 2026-05-21 16:39:39 UTC
- Host: Toto241 (Windows-10-10.0.26200-SP0)
- Python: 3.11.9
- Target: `tests`
- Laufzeit pytest: 173.42 s

**Entscheidung:** GO

## Gesamtuebersicht

| Status | Anzahl |
| --- | ---: |
| passed | 1279 |
| failed | 0 |
| error | 0 |
| skipped | 3 |
| **gesamt** | **1282** |
| Dauer (Summe) | 171.03 s |

## Abdeckung nach Konzept-Bereich (Anhang)

| Bereich (Anhang) | Tests | passed | failed | error | skipped | Dauer (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kapitel 2 / Anhang D - Mitglieder-Szenarien | 18 | 18 | 0 | 0 | 0 | 70.60 |
| Anhang D - Rollen- und Berechtigungsmatrix | 69 | 69 | 0 | 0 | 0 | 0.89 |
| Kapitel 3 / Anhang C - Pairwise-Matrix | 13 | 13 | 0 | 0 | 0 | 8.18 |
| Kapitel 8 - Property-/Fuzz-Tests | 29 | 29 | 0 | 0 | 0 | 9.95 |
| Teil II Abschnitt 11 - Negativtests | 48 | 48 | 0 | 0 | 0 | 10.58 |
| Teil II Abschnitt 12 - Datenschutztests | 280 | 280 | 0 | 0 | 0 | 2.65 |
| Teil II Abschnitt 11.3 D - Security-Negativtests | 22 | 22 | 0 | 0 | 0 | 0.03 |
| Play-Store-Sync (tools/playstore_sync.py) | 29 | 29 | 0 | 0 | 0 | 0.17 |
| Anhang J + J2 - Release-Gate | 335 | 335 | 0 | 0 | 0 | 18.90 |

## Ergebnisse pro Testdatei

| Datei | Tests | passed | failed | error | skipped | Dauer (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TestAssistantLogRotation | 1 | 1 | 0 | 0 | 0 | 0.37 |
| TestAutoBackup | 2 | 2 | 0 | 0 | 0 | 0.58 |
| TestBackupAndRestore | 3 | 3 | 0 | 0 | 0 | 0.62 |
| TestBackupSqlCipherPath | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestBuildHtml | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestBulkInsertPerformance | 3 | 3 | 0 | 0 | 0 | 7.07 |
| TestBulkOperations | 3 | 3 | 0 | 0 | 0 | 0.69 |
| TestCalendarNoMutation | 1 | 1 | 0 | 0 | 0 | 0.17 |
| TestCheck | 3 | 3 | 0 | 0 | 0 | 0.03 |
| TestCheckConsistency | 4 | 4 | 0 | 0 | 0 | 0.02 |
| TestCheckDataDeletion | 3 | 3 | 0 | 0 | 0 | 0.02 |
| TestCheckDemoData | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestCheckI18n | 1 | 1 | 0 | 0 | 0 | 0.01 |
| TestCheckPermissions | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestCheckSdkLevels | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestCheckSecrets | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestCheckVersioning | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestCodeSmells | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestCompleteTaskCatchUp | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestConversationHistory | 1 | 1 | 0 | 0 | 0 | 0.17 |
| TestCsvExport | 2 | 2 | 0 | 0 | 0 | 0.40 |
| TestCsvImportRoundTrip | 3 | 3 | 0 | 0 | 0 | 0.90 |
| TestCuratedQuality | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestDashboardSummary | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestDayStructurePersistence | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestDaysUntil | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestDeadlineCalculationPerformance | 1 | 1 | 0 | 0 | 0 | 0.12 |
| TestDefaultSecureStore | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestDeleteAllUserData | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestDeleteCapabilities | 4 | 4 | 0 | 0 | 0 | 0.76 |
| TestDeletionSupported | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestDestructiveFlags | 1 | 1 | 0 | 0 | 0 | 0.17 |
| TestDetectDeviceLanguage | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestDetectTrackingSdks | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestDiagnose | 1 | 1 | 0 | 0 | 0 | 1.05 |
| TestDisabledModuleSurfaced | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestEncryption | 2 | 2 | 0 | 0 | 0 | 0.20 |
| TestEuRegistry | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestFindPlaceholders | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestFingerprint | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestFormatCurrency | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestFormatMarkdown | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestGeminiAssistantStub | 2 | 2 | 0 | 0 | 0 | 0.46 |
| TestGeminiRealApi | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestGenerate | 3 | 3 | 0 | 0 | 0 | 0.02 |
| TestGenerateLocalizations | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestGroupByModule | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestGuiImports | 5 | 5 | 0 | 0 | 0 | 0.02 |
| TestHasCapabilityHonorsDisabled | 2 | 2 | 0 | 0 | 0 | 0.32 |
| TestHkdf | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestHttpSyncRoundTrip | 1 | 1 | 0 | 0 | 0 | 0.53 |
| TestHttpsSyncServer | 1 | 1 | 0 | 0 | 0 | 0.78 |
| TestI18n | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestI18nClass | 8 | 8 | 0 | 0 | 0 | 0.01 |
| TestI18nSyncTool | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestIcalExport | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestIcalImportRoundTrip | 2 | 2 | 0 | 0 | 0 | 0.57 |
| TestIdentity | 7 | 7 | 0 | 0 | 0 | 0.01 |
| TestImapAbruf | 1 | 1 | 0 | 0 | 0 | 0.23 |
| TestInMemorySecureStore | 8 | 8 | 0 | 0 | 0 | 0.01 |
| TestInboxExtractText | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestInputValidation | 6 | 6 | 0 | 0 | 0 | 1.10 |
| TestKeyringSecureStore | 4 | 4 | 0 | 0 | 0 | 0.11 |
| TestLamportCrdt | 3 | 3 | 0 | 0 | 0 | 0.20 |
| TestLanguageMenuItems | 7 | 7 | 0 | 0 | 0 | 0.02 |
| TestLicensing | 78 | 78 | 0 | 0 | 0 | 5.69 |
| TestLlmJsonParsing | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestLlmProposalValidation | 2 | 2 | 0 | 0 | 0 | 0.33 |
| TestLocaleFilesIntegrity | 5 | 5 | 0 | 0 | 0 | 0.03 |
| TestMainImports | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestModuleStatePersistence | 1 | 1 | 0 | 0 | 0 | 0.20 |
| TestNormalizeLanguage | 4 | 4 | 0 | 0 | 0 | 0.00 |
| TestNotesListingPerformance | 1 | 1 | 0 | 0 | 0 | 5.85 |
| TestNotesModule | 4 | 4 | 0 | 0 | 0 | 0.78 |
| TestOcrParsing | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestPairingFailures | 5 | 5 | 0 | 0 | 0 | 0.09 |
| TestPairingHappyPath | 3 | 3 | 0 | 0 | 0 | 0.09 |
| TestParseBuildozerSpec | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestPrintFileNoShell | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestPrinten | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestProfile | 7 | 7 | 0 | 0 | 0 | 0.41 |
| TestPropertyBasedSkipped | 1 | 0 | 0 | 0 | 1 | 0.00 |
| TestProposalUpdate | 3 | 3 | 0 | 0 | 0 | 0.57 |
| TestProposalsFlow | 1 | 1 | 0 | 0 | 0 | 0.23 |
| TestPurgeDirectories | 2 | 2 | 0 | 0 | 0 | 0.01 |
| TestRealRepo | 6 | 6 | 0 | 0 | 0 | 0.05 |
| TestRealRepoFallback | 4 | 4 | 0 | 0 | 0 | 0.01 |
| TestRecurrenceValidation | 5 | 5 | 0 | 0 | 0 | 0.91 |
| TestRegistry | 3 | 3 | 0 | 0 | 0 | 0.46 |
| TestRegistryGetCapability | 3 | 3 | 0 | 0 | 0 | 0.52 |
| TestRelativeWhen | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestReminderTriggering | 6 | 6 | 0 | 0 | 0 | 0.01 |
| TestReportFormats | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestResolveLanguage | 7 | 7 | 0 | 0 | 0 | 0.01 |
| TestReviewFixes | 18 | 18 | 0 | 0 | 0 | 7.57 |
| TestRunChecksIntegration | 2 | 2 | 0 | 0 | 0 | 0.16 |
| TestSandboxDataDirs | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestSearch | 3 | 3 | 0 | 0 | 0 | 0.60 |
| TestSecretsDoNotLeak | 1 | 1 | 0 | 0 | 0 | 0.02 |
| TestSettings | 4 | 4 | 0 | 0 | 0 | 0.65 |
| TestSmtpVersand | 4 | 4 | 0 | 0 | 0 | 0.01 |
| TestSmtpWiring | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestSqlCipherRealRoundTrip | 1 | 0 | 0 | 0 | 1 | 0.01 |
| TestSqlCipherValidation | 2 | 2 | 0 | 0 | 0 | 0.00 |
| TestStatistics | 5 | 5 | 0 | 0 | 0 | 1.04 |
| TestSyncCompaction | 1 | 1 | 0 | 0 | 0 | 0.03 |
| TestSyncExpandedCapabilities | 1 | 1 | 0 | 0 | 0 | 0.36 |
| TestSyncReentry | 2 | 2 | 0 | 0 | 0 | 0.39 |
| TestSyncServerCompaction | 1 | 1 | 0 | 0 | 0 | 0.57 |
| TestSyncServerTls | 1 | 1 | 0 | 0 | 0 | 0.00 |
| TestThreadSafety | 1 | 1 | 0 | 0 | 0 | 0.70 |
| TestTranscript | 7 | 7 | 0 | 0 | 0 | 0.01 |
| TestTranslationResolution | 3 | 3 | 0 | 0 | 0 | 0.01 |
| TestTruncate | 3 | 3 | 0 | 0 | 0 | 0.00 |
| TestUrgencyColor | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestUtcTimestamps | 1 | 1 | 0 | 0 | 0 | 0.18 |
| TestUtcTimestampsInDb | 2 | 2 | 0 | 0 | 0 | 0.40 |
| TestVCardExport | 1 | 1 | 0 | 0 | 0 | 0.19 |
| TestVCardImportRoundTrip | 1 | 1 | 0 | 0 | 0 | 0.35 |
| TestValidateLocalizations | 5 | 5 | 0 | 0 | 0 | 0.01 |
| TestWipeAllData | 3 | 3 | 0 | 0 | 0 | 0.54 |
| TestYearlyPdfReport | 1 | 1 | 0 | 0 | 0 | 0.20 |
| test_build_status | 17 | 17 | 0 | 0 | 0 | 1.95 |
| test_control_panel | 14 | 14 | 0 | 0 | 0 | 0.94 |
| test_dashboard_generator | 20 | 20 | 0 | 0 | 0 | 3.43 |
| test_gitignore_completeness | 82 | 82 | 0 | 0 | 0 | 1.50 |
| test_gui_free_tier_boot | 2 | 2 | 0 | 0 | 0 | 5.43 |
| test_gui_refresh_guards | 16 | 16 | 0 | 0 | 0 | 0.79 |
| test_gui_widget_guards | 3 | 3 | 0 | 0 | 0 | 3.56 |
| test_md_to_html | 15 | 15 | 0 | 0 | 0 | 0.01 |
| test_members_scenarios | 18 | 18 | 0 | 0 | 0 | 70.60 |
| test_negative_inputs | 40 | 40 | 0 | 0 | 0 | 7.45 |
| test_negative_network | 8 | 8 | 0 | 0 | 0 | 3.13 |
| test_negative_security | 22 | 22 | 0 | 0 | 0 | 0.03 |
| test_pairwise_matrix | 13 | 13 | 0 | 0 | 0 | 8.18 |
| test_playstore_sync | 29 | 29 | 0 | 0 | 0 | 0.17 |
| test_privacy_data_rights | 10 | 10 | 0 | 0 | 0 | 2.13 |
| test_privacy_scan | 270 | 270 | 0 | 0 | 0 | 0.53 |
| test_properties_concept | 29 | 29 | 0 | 0 | 0 | 9.95 |
| test_protocol_generator | 4 | 4 | 0 | 0 | 0 | 0.07 |
| test_release_gate | 10 | 10 | 0 | 0 | 0 | 1.04 |
| test_release_gate_extended | 152 | 152 | 0 | 0 | 0 | 0.18 |
| test_roles_permissions | 69 | 69 | 0 | 0 | 0 | 0.89 |

## Vollstaendige Test-Liste

| Status | Test-ID | Dauer (s) |
| --- | --- | ---: |
| [pass] | `tests.concept.test_build_status::test_build_center_in_dashboard_html` | 0.266 |
| [pass] | `tests.concept.test_build_status::test_build_center_links_point_to_real_scripts` | 0.262 |
| [pass] | `tests.concept.test_build_status::test_build_center_section_in_index_html` | 0.175 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-android.bat]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-android.sh]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-desktop.bat]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-desktop.sh]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_build_scripts_present[build-ios.sh]` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_buildozer_spec_present_for_android` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_each_item_has_required_fields` | 0.169 |
| [pass] | `tests.concept.test_build_status::test_gather_returns_three_platforms` | 0.178 |
| [pass] | `tests.concept.test_build_status::test_index_build_center_renders_three_cards` | 0.171 |
| [pass] | `tests.concept.test_build_status::test_index_build_center_uses_clipboard_helper` | 0.178 |
| [pass] | `tests.concept.test_build_status::test_main_json_runs` | 0.196 |
| [pass] | `tests.concept.test_build_status::test_main_plain_text_runs` | 0.175 |
| [pass] | `tests.concept.test_build_status::test_pyinstaller_spec_present_for_desktop` | 0.001 |
| [pass] | `tests.concept.test_build_status::test_to_dict_is_json_serializable` | 0.173 |
| [pass] | `tests.concept.test_control_panel::test_actions_build_lists_three_platforms_indirectly` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_actions_build_uses_existing_scripts` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_actions_playstore_complete` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_actions_tests_call_python_modules` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_actions_tests_complete` | 0.082 |
| [pass] | `tests.concept.test_control_panel::test_command_runner_busy_flag` | 0.414 |
| [pass] | `tests.concept.test_control_panel::test_command_runner_returns_nonzero_on_failure` | 0.085 |
| [pass] | `tests.concept.test_control_panel::test_command_runner_streams_and_signals_done` | 0.087 |
| [pass] | `tests.concept.test_control_panel::test_destructive_actions_have_confirm_prompt` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_link_targets_are_known_repo_paths` | 0.003 |
| [pass] | `tests.concept.test_control_panel::test_links_point_to_known_paths` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_start_bat_checks_customtkinter` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_start_bat_invokes_control_panel` | 0.001 |
| [pass] | `tests.concept.test_control_panel::test_window_can_be_constructed_and_destroyed` | 0.259 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket0-go]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket1-block]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket2-block]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket3-hold]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_bucket_status[bucket4-unknown]` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_decision_status_mapping` | 0.001 |
| [pass] | `tests.concept.test_dashboard_generator::test_default_paths_inside_reports_dir` | 0.000 |
| [pass] | `tests.concept.test_dashboard_generator::test_failure_section_shows_when_records_failed` | 0.216 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_contains_all_records` | 0.263 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_does_not_contain_nested_anchors` | 0.259 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_escapes_html_in_test_id` | 0.224 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_has_kpi_for_each_marker` | 0.258 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_has_navigation` | 0.259 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_is_self_contained` | 0.263 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_links_to_companion_artifacts` | 0.259 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_renders_decision_pill` | 0.257 |
| [pass] | `tests.concept.test_dashboard_generator::test_html_renders_skipped_as_hold` | 0.255 |
| [pass] | `tests.concept.test_dashboard_generator::test_main_handles_missing_input` | 0.003 |
| [pass] | `tests.concept.test_dashboard_generator::test_main_runs_against_real_protocol` | 0.472 |
| [pass] | `tests.concept.test_dashboard_generator::test_render_dashboard_is_deterministic` | 0.433 |
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
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.AppImage]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.aab]` | 0.031 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.apk]` | 0.029 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.deb]` | 0.031 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.dll]` | 0.032 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.dmg]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.dylib]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.exe]` | 0.044 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.ipa]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.jks]` | 0.029 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.keystore]` | 0.029 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.msi]` | 0.029 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.pyd]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.rpm]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_build_binary_is_tracked[.so]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_no_dist_or_build_folder_tracked` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[.DS_Store]` | 0.029 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[.buildozer/android/platform/build.cfg]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[.coverage]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[.pytest_cache/v/cache/lastfailed]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[Alltagshelfer-ios/Pods/Manifest.lock]` | 0.033 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[Alltagshelfer-ios/xcuserdata/torst.xcuserdatad/UserInterfaceState.xcuserstate]` | 0.034 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[Alltagshelfer.exe]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[DerivedData/Build/Products/Debug.app/Foo]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[Thumbs.db]` | 0.029 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[alltagshelfer.db]` | 0.031 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[ausgaben/2026-05.pdf]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[backups/2026-05.tar.gz]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[bin/alltagshelfer-0.9.0-arm64-v8a-debug.apk]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[build/anything/at/any/depth.py]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[build/foo.txt]` | 0.031 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/Alltagshelfer/Alltagshelfer.exe]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/Alltagshelfer/_internal/_tcl_data/tcl8.6/init.tcl]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/Alltagshelfer/_internal/cryptography/hazmat/_oid.cpython-311.dll]` | 0.032 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/Alltagshelfer/_internal/python311.dll]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[dist/something.dmg]` | 0.031 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[htmlcov/index.html]` | 0.029 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[logs/app.log]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[playstore.local.json]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.AppImage]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.aab]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.deb]` | 0.031 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.ipa]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.jks]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[release.keystore]` | 0.030 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[test.sqlite]` | 0.031 |
| [pass] | `tests.concept.test_gitignore_completeness::test_path_is_ignored_by_git[tools/__pycache__/dashboard.cpython-311.pyc]` | 0.029 |
| [pass] | `tests.concept.test_gitignore_completeness::test_playstore_local_json_not_tracked` | 0.029 |
| [pass] | `tests.concept.test_gui_free_tier_boot::test_gui_boots_in_free_tier_without_crash` | 2.778 |
| [pass] | `tests.concept.test_gui_free_tier_boot::test_gui_boots_with_default_license_too` | 2.652 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_all_refresh_methods_are_guarded` | 0.041 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_calendar]` | 0.044 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_contracts]` | 0.041 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_dashboard]` | 0.069 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_finance]` | 0.067 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_history]` | 0.041 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_inbox]` | 0.065 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_members]` | 0.041 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_module_admin]` | 0.064 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_orders]` | 0.041 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_shopping]` | 0.039 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_social]` | 0.040 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_statistics]` | 0.040 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_status]` | 0.041 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_method_has_hasattr_guard[_refresh_tasks]` | 0.068 |
| [pass] | `tests.concept.test_gui_refresh_guards::test_refresh_methods_exist` | 0.045 |
| [pass] | `tests.concept.test_gui_widget_guards::test_can_load_gui_module_source` | 0.048 |
| [pass] | `tests.concept.test_gui_widget_guards::test_chat_methods_are_guarded` | 0.438 |
| [pass] | `tests.concept.test_gui_widget_guards::test_methods_in_init_path_have_widget_guards` | 3.074 |
| [pass] | `tests.concept.test_md_to_html::test_doc_wrapper_back_link` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_doc_wrapper_includes_dashboard_css` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_escapes_html_in_paragraphs` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_inline_code_protects_from_bold` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_blockquote` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_bold_italic_code` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_fenced_code_block` | 0.000 |
| [pass] | `tests.concept.test_md_to_html::test_renders_h2_to_h6` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_headings_with_anchors` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_hr` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_link` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_ordered_list` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_paragraphs` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_table` | 0.001 |
| [pass] | `tests.concept.test_md_to_html::test_renders_unordered_list` | 0.001 |
| [pass] | `tests.concept.test_members_scenarios::test_M01_single_owner_no_rotation` | 0.330 |
| [pass] | `tests.concept.test_members_scenarios::test_M02_minimal_team_two_members` | 0.908 |
| [pass] | `tests.concept.test_members_scenarios::test_M05_meets_play_minimum_12` | 8.479 |
| [pass] | `tests.concept.test_members_scenarios::test_M06_scales_to_twenty_plus` | 6.063 |
| [pass] | `tests.concept.test_members_scenarios::test_M07_mixed_status_distribution` | 4.246 |
| [pass] | `tests.concept.test_members_scenarios::test_M08_invited_only_owner_active` | 0.552 |
| [pass] | `tests.concept.test_members_scenarios::test_M09_reactivation_restores_member` | 1.192 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-01]` | 0.484 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-02]` | 0.972 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-03]` | 1.839 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-04]` | 3.487 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-05]` | 4.235 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-06]` | 6.085 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-07]` | 4.553 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-08]` | 0.605 |
| [pass] | `tests.concept.test_members_scenarios::test_M_can_seed_profile[M-09]` | 1.201 |
| [pass] | `tests.concept.test_members_scenarios::test_get_events_handles_all_sizes` | 23.638 |
| [pass] | `tests.concept.test_members_scenarios::test_remove_and_readd_preserves_distinct_id` | 1.735 |
| [pass] | `tests.concept.test_negative_inputs::test_NA02_long_contract_name_does_not_break_listing` | 0.189 |
| [pass] | `tests.concept.test_negative_inputs::test_NA02_long_member_name_is_stored_or_rejected[10000]` | 0.149 |
| [pass] | `tests.concept.test_negative_inputs::test_NA02_long_member_name_is_stored_or_rejected[1024]` | 0.210 |
| [pass] | `tests.concept.test_negative_inputs::test_NA02_long_member_name_is_stored_or_rejected[65536]` | 0.155 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description["Anna' DROP"]` | 0.194 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['  trailing space   ']` | 0.186 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description[' ']` | 0.168 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['<script>alert(1)</scrip]` | 0.209 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['Anna \U0001f600']` | 0.187 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['Anna\\nMehrzeilig']` | 0.201 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['Anna\\x00Nachher']` | 0.178 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['\\u202earabicRTL']` | 0.204 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['\u0410\u043d\u043d\u0430 \u0418\u0432\u0430\u043d\u043e\u0432\u0430']` | 0.178 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_expense_description['\u5c71\u7530\u592a\u90ce']` | 0.193 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name["Anna' DROP"]` | 0.206 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['  trailing space   ']` | 0.201 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name[' ']` | 0.165 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['<script>alert(1)</scrip]` | 0.192 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['Anna \U0001f600']` | 0.162 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['Anna\\nMehrzeilig']` | 0.189 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['Anna\\x00Nachher']` | 0.179 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['\\u202earabicRTL']` | 0.181 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['\u0410\u043d\u043d\u0430 \u0418\u0432\u0430\u043d\u043e\u0432\u0430']` | 0.172 |
| [pass] | `tests.concept.test_negative_inputs::test_NA03_special_chars_in_member_name['\u5c71\u7530\u592a\u90ce']` | 0.174 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[%27%20OR%201=1%20--%]` | 0.182 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields['); DELETE FROM cont]` | 0.186 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[1' OR '1'='1]` | 0.149 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[Anna"; UPDATE family]` | 0.179 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[Anna'; DROP TABLE fa]` | 0.167 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_contract_fields[Anna\\'; SELECT * FRO]` | 0.193 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[%27%20OR%201=1%20--%]` | 0.193 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal['); DELETE FROM cont]` | 0.203 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[1' OR '1'='1]` | 0.189 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[Anna"; UPDATE family]` | 0.198 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[Anna'; DROP TABLE fa]` | 0.192 |
| [pass] | `tests.concept.test_negative_inputs::test_NA04_sql_injection_in_member_name_is_literal[Anna\\'; SELECT * FRO]` | 0.210 |
| [pass] | `tests.concept.test_negative_inputs::test_NA05_double_member_is_idempotent_or_distinct_ids` | 0.193 |
| [pass] | `tests.concept.test_negative_inputs::test_NA11_invalid_param_type_does_not_crash` | 0.212 |
| [pass] | `tests.concept.test_negative_inputs::test_NA11_missing_required_param_returns_friendly_error` | 0.197 |
| [pass] | `tests.concept.test_negative_inputs::test_NA11_unknown_capability_returns_friendly_error` | 0.186 |
| [pass] | `tests.concept.test_negative_network::test_NB01_unreachable_server_does_not_corrupt_state` | 2.042 |
| [pass] | `tests.concept.test_negative_network::test_NB04_garbage_response_is_handled` | 0.520 |
| [pass] | `tests.concept.test_negative_network::test_NB04_server_500_does_not_silently_succeed` | 0.518 |
| [pass] | `tests.concept.test_negative_network::test_NB06_corrupt_log_lines_are_skipped` | 0.009 |
| [pass] | `tests.concept.test_negative_network::test_NB06_offline_then_sync_round_trips_events` | 0.024 |
| [pass] | `tests.concept.test_negative_network::test_NB07_lww_orders_by_lamport_then_time` | 0.016 |
| [pass] | `tests.concept.test_negative_network::test_lamport_observe_clamps_negative_input` | 0.001 |
| [pass] | `tests.concept.test_negative_network::test_sync_event_from_dict_handles_missing_fields` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_ND04_swapped_signing_key_is_rejected` | 0.001 |
| [pass] | `tests.concept.test_negative_security::test_ND04_tampered_payload_is_rejected` | 0.004 |
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
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_has_acceptable_size` | 0.000 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_is_deterministic` | 1.696 |
| [pass] | `tests.concept.test_pairwise_matrix::test_matrix_respects_constraints` | 0.868 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[0]` | 0.692 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[100]` | 0.980 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[125]` | 0.879 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[150]` | 0.664 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[175]` | 0.278 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[25]` | 0.858 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[50]` | 0.492 |
| [pass] | `tests.concept.test_pairwise_matrix::test_sampled_cases_persist_in_real_repo[75]` | 0.770 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_export_writes_snapshot` | 0.022 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_init_writes_yaml` | 0.009 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_push_aborts_on_invalid` | 0.004 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_push_dry_run_and_pull_via_mock` | 0.049 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_sample_prints_yaml` | 0.015 |
| [pass] | `tests.concept.test_playstore_sync::test_cli_validate_on_sample` | 0.017 |
| [pass] | `tests.concept.test_playstore_sync::test_default_yaml_in_repo_is_valid` | 0.027 |
| [pass] | `tests.concept.test_playstore_sync::test_diff_keys_empty_when_equal` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_diff_keys_reports_added_and_removed` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_diff_keys_reports_changed_strings` | 0.000 |
| [pass] | `tests.concept.test_playstore_sync::test_export_markdown_contains_all_sections` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_export_markdown_shows_length_counters` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_init_from_repo_has_required_top_level` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_init_from_repo_picks_up_buildozer_settings` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_invalid_package_name_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_invalid_release_status_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_merge_keeps_local_when_remote_empty` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_merge_prefers_remote_when_not_empty` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_missing_internet_permission_is_warning` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_missing_top_level_keys_are_errors` | 0.000 |
| [pass] | `tests.concept.test_playstore_sync::test_mock_dry_run_does_not_modify_state` | 0.002 |
| [pass] | `tests.concept.test_playstore_sync::test_mock_pull_unknown_package_raises` | 0.002 |
| [pass] | `tests.concept.test_playstore_sync::test_mock_roundtrip_persists_and_returns_identical` | 0.003 |
| [pass] | `tests.concept.test_playstore_sync::test_permission_overlap_declared_blocked_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_sample_config_validates_clean` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_too_long_full_description_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_too_long_short_description_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_too_long_title_is_error` | 0.001 |
| [pass] | `tests.concept.test_playstore_sync::test_user_fraction_out_of_range_is_error` | 0.001 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB02_purging_member_decouples_references` | 0.193 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_calendar-termine.csv-calendar]` | 0.199 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_contracts-vertraege.csv-contracts]` | 0.186 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_expenses-ausgaben.csv-expenses]` | 0.193 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_family-haushalt.csv-family]` | 0.209 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_each_exporter_produces_header[export_social-kontakte.csv-social]` | 0.234 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB03_export_all_produces_parseable_artifacts` | 0.179 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB04_soft_delete_hides_then_restore_brings_back` | 0.184 |
| [pass] | `tests.concept.test_privacy_data_rights::test_PB06_dropping_db_file_removes_all_data` | 0.353 |
| [pass] | `tests.concept.test_privacy_data_rights::test_audit_log_format_does_not_leak_pii` | 0.196 |
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
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[mobile/screens/more.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[models.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/family.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/inbox.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/social.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/data_deletion.py]` | 0.001 |
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
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/sync_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[services/vcard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/build_status.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/control_panel.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/data_safety.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_JS02_no_hardcoded_secrets[tools/gen_api_doc.py]` | 0.001 |
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
| [pass] | `tests.concept.test_privacy_scan::test_PB01_account_deletion_capability_exists` | 0.244 |
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
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[mobile/screens/more.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[models.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/family.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/inbox.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/social.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/data_deletion.py]` | 0.001 |
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
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/sync_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[services/vcard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/build_status.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/control_panel.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/data_safety.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD01_no_cleartext_http_urls[tools/gen_api_doc.py]` | 0.001 |
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
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[database.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[diagnose.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[gui.py]` | 0.004 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[main.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/app.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[mobile/screens/more.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[models.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/family.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/inbox.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/social.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/data_deletion.py]` | 0.001 |
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
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/licensing.py]` | 0.002 |
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
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/sync_server.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[services/vcard.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/build_status.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/control_panel.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/dashboard.py]` | 0.002 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/data_safety.py]` | 0.001 |
| [pass] | `tests.concept.test_privacy_scan::test_PD04_no_pii_in_log_statements[tools/gen_api_doc.py]` | 0.001 |
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
| [pass] | `tests.concept.test_properties_concept::test_P1_rotation_advances_one_step` | 4.317 |
| [pass] | `tests.concept.test_properties_concept::test_P2_overdue_task_rolls_forward_to_future` | 3.899 |
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
| [pass] | `tests.concept.test_properties_concept::test_P6_pairwise_deterministic` | 1.712 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_artifacts_present_after_run` | 0.013 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_classifies_and_decides` | 0.003 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_formats_markdown` | 0.054 |
| [pass] | `tests.concept.test_protocol_generator::test_protocol_parses_junit` | 0.003 |
| [pass] | `tests.concept.test_release_gate::test_J10_full_module_registry_assembles` | 0.152 |
| [pass] | `tests.concept.test_release_gate::test_J1_version_code_is_positive_integer` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J2_privacy_documents_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J3_license_file_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J4_playstore_doc_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J5_testing_doc_present` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J6_concept_modules_import` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J7_pairwise_matrix_has_full_coverage` | 0.884 |
| [pass] | `tests.concept.test_release_gate::test_J8_permission_matrix_is_complete` | 0.001 |
| [pass] | `tests.concept.test_release_gate::test_J9_member_profiles_present` | 0.000 |
| [pass] | `tests.concept.test_release_gate_extended::test_JG04_playstore_doc_covers_section[Closed]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JG04_playstore_doc_covers_section[Datenschutz]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JG04_playstore_doc_covers_section[Produktionsfreigabe]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JG04_playstore_doc_covers_section[Voraussetzungen]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JP01_privacy_policy_linked_in_playstore_doc` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JQ01_concept_markers_registered` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[assistant.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[core/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[core/interface.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[database.py]` | 0.004 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[diagnose.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[gui.py]` | 0.009 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[main.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/app.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[mobile/screens/more.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[models.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/calendar.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/contracts.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/family.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/finance.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/inbox.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/social.py]` | 0.002 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/data_deletion.py]` | 0.001 |
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
| [pass] | `tests.concept.test_release_gate_extended::test_JS03_no_debug_features_in_release_code[services/sync_server.py]` | 0.001 |
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
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/helpers.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/dashboard.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[mobile/screens/more.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[models.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/calendar.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/contracts.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/daystructure.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/family.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/finance.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/inbox.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/notes.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/search.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/social.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/statistics.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[modules/templates.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/__init__.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/activation_flow.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/backup.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/config.py]` | 0.001 |
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/data_deletion.py]` | 0.001 |
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
| [pass] | `tests.concept.test_release_gate_extended::test_JT04_no_blocker_todo[services/sync_server.py]` | 0.001 |
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
| [pass] | `tests.concept.test_roles_permissions::test_destructive_capabilities_have_marker` | 0.162 |
| [pass] | `tests.concept.test_roles_permissions::test_guest_cannot_modify_data` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_license_gate_blocks_ai_in_free` | 0.159 |
| [pass] | `tests.concept.test_roles_permissions::test_license_gate_blocks_finance_writes_in_free` | 0.167 |
| [pass] | `tests.concept.test_roles_permissions::test_license_gate_passes_family_in_free` | 0.165 |
| [pass] | `tests.concept.test_roles_permissions::test_member_can_self_assign_but_not_other` | 0.000 |
| [pass] | `tests.concept.test_roles_permissions::test_owner_can_do_everything` | 0.001 |
| [pass] | `tests.concept.test_roles_permissions::test_owner_concept_role_maps_to_pro_license` | 0.173 |
| [pass] | `tests.test_data_deletion.TestDeleteAllUserData::test_end_to_end` | 0.191 |
| [pass] | `tests.test_data_deletion.TestPurgeDirectories::test_missing_dir_is_skipped` | 0.001 |
| [pass] | `tests.test_data_deletion.TestPurgeDirectories::test_removes_files_keeps_root` | 0.005 |
| [pass] | `tests.test_data_deletion.TestSandboxDataDirs::test_builds_subdir_paths` | 0.001 |
| [pass] | `tests.test_data_deletion.TestWipeAllData::test_clears_all_tables` | 0.167 |
| [pass] | `tests.test_data_deletion.TestWipeAllData::test_include_settings_false_keeps_settings` | 0.171 |
| [pass] | `tests.test_data_deletion.TestWipeAllData::test_schema_survives_wipe` | 0.203 |
| [pass] | `tests.test_data_safety.TestCheckConsistency::test_analytics_purpose_without_sdk_is_error` | 0.007 |
| [pass] | `tests.test_data_safety.TestCheckConsistency::test_clean_declaration_passes` | 0.007 |
| [pass] | `tests.test_data_safety.TestCheckConsistency::test_false_sharing_is_error` | 0.007 |
| [pass] | `tests.test_data_safety.TestCheckConsistency::test_missing_deletion_warns` | 0.002 |
| [pass] | `tests.test_data_safety.TestDeletionSupported::test_false_without_service` | 0.002 |
| [pass] | `tests.test_data_safety.TestDeletionSupported::test_true_when_present` | 0.007 |
| [pass] | `tests.test_data_safety.TestDetectTrackingSdks::test_detects_firebase` | 0.004 |
| [pass] | `tests.test_data_safety.TestDetectTrackingSdks::test_detects_sentry` | 0.003 |
| [pass] | `tests.test_data_safety.TestDetectTrackingSdks::test_none_for_clean_deps` | 0.003 |
| [pass] | `tests.test_data_safety.TestFormatMarkdown::test_contains_table` | 0.001 |
| [pass] | `tests.test_data_safety.TestGenerate::test_clean_app_shares_nothing` | 0.007 |
| [pass] | `tests.test_data_safety.TestGenerate::test_deletion_missing_reflected` | 0.002 |
| [pass] | `tests.test_data_safety.TestGenerate::test_tracking_dep_flips_shared` | 0.007 |
| [pass] | `tests.test_data_safety.TestRealRepo::test_real_app_has_no_tracking` | 0.001 |
| [pass] | `tests.test_data_safety.TestRealRepo::test_real_playstore_yml_is_consistent` | 0.011 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_geometry_helpers` | 0.004 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_gui_has_license_section_methods` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_gui_module_imports` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_license_ui_helpers_callable_headless` | 0.011 |
| [pass] | `tests.test_gui_smoke.TestGuiImports::test_main_app_class_exists` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestMainImports::test_build_registry_signature` | 0.001 |
| [pass] | `tests.test_gui_smoke.TestMainImports::test_main_module_imports` | 0.001 |
| [pass] | `tests.test_i18n.TestDetectDeviceLanguage::test_lang_fallback_when_no_language` | 0.003 |
| [pass] | `tests.test_i18n.TestDetectDeviceLanguage::test_priority_language_over_lang` | 0.003 |
| [pass] | `tests.test_i18n.TestDetectDeviceLanguage::test_reads_language_env` | 0.002 |
| [pass] | `tests.test_i18n.TestEuRegistry::test_24_official_languages` | 0.001 |
| [pass] | `tests.test_i18n.TestEuRegistry::test_codes_are_two_letters` | 0.001 |
| [pass] | `tests.test_i18n.TestEuRegistry::test_default_is_first` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_auto_resolves` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_available_languages_includes_default` | 0.003 |
| [pass] | `tests.test_i18n.TestI18nClass::test_default_german` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_missing_key_falls_back_to_default_lang` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_translation_lookup` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_unknown_key_returns_default_arg` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_unknown_key_returns_key` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nClass::test_unknown_language_falls_back_to_default` | 0.001 |
| [pass] | `tests.test_i18n.TestI18nSyncTool::test_all_eu_languages_have_files` | 0.002 |
| [pass] | `tests.test_i18n.TestI18nSyncTool::test_check_passes` | 0.006 |
| [pass] | `tests.test_i18n.TestI18nSyncTool::test_coverage_numbers` | 0.007 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_core_keys_present_everywhere` | 0.006 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_every_file_is_valid_json` | 0.008 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_full_languages_have_complete_parity` | 0.002 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_no_locale_has_extra_keys` | 0.005 |
| [pass] | `tests.test_i18n.TestLocaleFilesIntegrity::test_placeholders_preserved_in_full_languages` | 0.004 |
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
| [pass] | `tests.test_integration.TestHttpsSyncServer::test_tls_handshake_with_self_signed_cert` | 0.780 |
| [pass] | `tests.test_integration.TestImapAbruf::test_fetch_imap_loops_through_unseen` | 0.226 |
| [pass] | `tests.test_integration.TestOcrParsing::test_missing_engine_returns_hint` | 0.003 |
| [pass] | `tests.test_integration.TestOcrParsing::test_receipt_text_extraction` | 0.002 |
| [pass] | `tests.test_integration.TestPrinten::test_print_file_calls_lpr_on_macos` | 0.002 |
| [pass] | `tests.test_integration.TestPrinten::test_print_file_calls_subprocess_on_unix` | 0.002 |
| [pass] | `tests.test_integration.TestPrinten::test_print_file_missing_returns_error` | 0.001 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_calls_protocol` | 0.007 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_handles_server_error` | 0.002 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_skips_starttls_when_disabled` | 0.004 |
| [pass] | `tests.test_integration.TestSmtpVersand::test_send_smtp_without_config_returns_skip` | 0.001 |
| [pass] | `tests.test_legal.TestRealRepoFallback::test_all_docs_resolve_to_german` | 0.002 |
| [pass] | `tests.test_legal.TestRealRepoFallback::test_coverage_lists_german` | 0.003 |
| [pass] | `tests.test_legal.TestRealRepoFallback::test_legal_path_points_at_existing_file` | 0.001 |
| [pass] | `tests.test_legal.TestRealRepoFallback::test_unknown_language_falls_back_to_german` | 0.001 |
| [pass] | `tests.test_legal.TestTranslationResolution::test_missing_doc_returns_none` | 0.002 |
| [pass] | `tests.test_legal.TestTranslationResolution::test_prefers_translation_when_present` | 0.005 |
| [pass] | `tests.test_legal.TestTranslationResolution::test_translation_dir_without_doc_falls_back` | 0.003 |
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
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_auto_selected` | 0.002 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_contains_all_available_languages` | 0.002 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_default_selects_english` | 0.001 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_exactly_one_selected` | 0.007 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_first_entry_is_auto` | 0.002 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_region_code_normalized` | 0.002 |
| [pass] | `tests.test_mobile_helpers.TestLanguageMenuItems::test_unknown_setting_falls_back_to_default` | 0.002 |
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
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_delete_removes_from_list` | 0.049 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_list_keys_returns_set_keys` | 0.043 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_manifest_key_is_reserved` | 0.002 |
| [pass] | `tests.test_pairing.TestKeyringSecureStore::test_roundtrip` | 0.019 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_default_length_32` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_deterministic` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_distinct_inputs_distinct_outputs` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestHkdf::test_rejects_bad_length` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_calls_in_wrong_order_raise` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_initiator_cannot_make_proof_before_learning_responder_key` | 0.023 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_rejects_bad_signature_length` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_responder_with_wrong_initiator_pubkey_in_invitation` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingFailures::test_wrong_ot_secret_breaks_handshake` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingHappyPath::test_both_sides_derive_same_psk` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingHappyPath::test_each_side_learns_the_other_public_key` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestPairingHappyPath::test_psk_symmetric_under_role_swap` | 0.043 |
| [pass] | `tests.test_pairing_handshake.TestSecretsDoNotLeak::test_result_only_exposes_safe_fields` | 0.022 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_deterministic` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_field_swap_does_not_collide` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_method_change_changes_transcript` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_rejects_empty_method_or_sid` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_rejects_negative_or_huge_exp` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_rejects_wrong_pubkey_length` | 0.001 |
| [pass] | `tests.test_pairing_handshake.TestTranscript::test_transcript_hash_is_32_bytes` | 0.001 |
| [pass] | `tests.test_performance.TestBulkInsertPerformance::test_insert_500_contracts_under_15s` | 2.963 |
| [pass] | `tests.test_performance.TestBulkInsertPerformance::test_insert_500_expenses_under_15s` | 2.911 |
| [pass] | `tests.test_performance.TestBulkInsertPerformance::test_list_200_contracts_under_2s` | 1.195 |
| [pass] | `tests.test_performance.TestDeadlineCalculationPerformance::test_deadline_calculation_scales` | 0.123 |
| [pass] | `tests.test_performance.TestNotesListingPerformance::test_list_attached_in_large_dataset` | 5.850 |
| [pass] | `tests.test_playstore_check.TestCheckDataDeletion::test_fails_when_service_missing` | 0.005 |
| [pass] | `tests.test_playstore_check.TestCheckDataDeletion::test_fails_when_wipe_method_missing` | 0.006 |
| [pass] | `tests.test_playstore_check.TestCheckDataDeletion::test_passes_when_mechanism_present` | 0.006 |
| [pass] | `tests.test_playstore_check.TestCheckDemoData::test_fails_when_db_missing` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckDemoData::test_passes_when_db_and_sqlite_excluded` | 0.001 |
| [pass] | `tests.test_playstore_check.TestCheckI18n::test_real_repo_parity_passes` | 0.008 |
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
| [pass] | `tests.test_playstore_check.TestCodeSmells::test_print_only_in_mobile_path` | 0.004 |
| [pass] | `tests.test_playstore_check.TestCodeSmells::test_requests_verify_false_is_smell` | 0.006 |
| [pass] | `tests.test_playstore_check.TestParseBuildozerSpec::test_extracts_app_block` | 0.002 |
| [pass] | `tests.test_playstore_check.TestParseBuildozerSpec::test_handles_missing_file` | 0.001 |
| [pass] | `tests.test_playstore_check.TestParseBuildozerSpec::test_ignores_comments_and_blanks` | 0.002 |
| [pass] | `tests.test_playstore_check.TestReportFormats::test_json_format_valid` | 0.001 |
| [pass] | `tests.test_playstore_check.TestReportFormats::test_summary_counts` | 0.001 |
| [pass] | `tests.test_playstore_check.TestRunChecksIntegration::test_runs_without_exception` | 0.154 |
| [pass] | `tests.test_playstore_check.TestRunChecksIntegration::test_subset_only` | 0.005 |
| [pass] | `tests.test_privacy_policy.TestBuildHtml::test_renders_markdown` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestBuildHtml::test_self_contained_document` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestCheck::test_finalized_policy_no_warning_about_placeholders` | 0.016 |
| [pass] | `tests.test_privacy_policy.TestCheck::test_missing_file_is_error` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestCheck::test_placeholders_warn` | 0.016 |
| [pass] | `tests.test_privacy_policy.TestFindPlaceholders::test_clean_text_returns_empty` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestFindPlaceholders::test_detects_template_tokens` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestFindPlaceholders::test_ignores_markdown_links` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestFindPlaceholders::test_unique_and_sorted` | 0.001 |
| [pass] | `tests.test_privacy_policy.TestRealRepo::test_real_build_produces_article` | 0.002 |
| [pass] | `tests.test_privacy_policy.TestRealRepo::test_real_check_has_no_errors` | 0.010 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_future_event_phrasing` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_multiple_due_events_all_trigger` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_new_event_after_first_check_still_fires` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_overdue_event_phrasing` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_reminder_not_repeated_on_recheck` | 0.001 |
| [pass] | `tests.test_scheduler_reminders.TestReminderTriggering::test_today_event_phrasing` | 0.001 |
| [pass] | `tests.test_smoke.TestAssistantLogRotation::test_log_does_not_grow_unbounded` | 0.374 |
| [pass] | `tests.test_smoke.TestAutoBackup::test_prune_old_backups_keeps_newest` | 0.266 |
| [pass] | `tests.test_smoke.TestAutoBackup::test_run_once_creates_backup_and_prunes` | 0.316 |
| [pass] | `tests.test_smoke.TestBackupAndRestore::test_list_backups_sorted_newest_first` | 0.266 |
| [pass] | `tests.test_smoke.TestBackupAndRestore::test_online_backup_creates_readable_copy` | 0.172 |
| [pass] | `tests.test_smoke.TestBackupAndRestore::test_restore_overwrites_live_db` | 0.187 |
| [pass] | `tests.test_smoke.TestBackupSqlCipherPath::test_sqlcipher_path_rejects_short_key` | 0.002 |
| [pass] | `tests.test_smoke.TestBackupSqlCipherPath::test_sqlcipher_path_requires_key` | 0.001 |
| [pass] | `tests.test_smoke.TestBulkOperations::test_bulk_complete_overdue_tasks` | 0.214 |
| [pass] | `tests.test_smoke.TestBulkOperations::test_bulk_delete_archived` | 0.239 |
| [pass] | `tests.test_smoke.TestBulkOperations::test_bulk_reject_open_proposals` | 0.238 |
| [pass] | `tests.test_smoke.TestCalendarNoMutation::test_recurring_event_not_mutated_in_db` | 0.167 |
| [pass] | `tests.test_smoke.TestCompleteTaskCatchUp::test_overdue_task_advances_rotation_multiple_times` | 0.190 |
| [pass] | `tests.test_smoke.TestConversationHistory::test_history_grows_across_calls` | 0.174 |
| [pass] | `tests.test_smoke.TestCsvExport::test_export_all_writes_five_files` | 0.204 |
| [pass] | `tests.test_smoke.TestCsvExport::test_export_contracts_writes_csv` | 0.196 |
| [pass] | `tests.test_smoke.TestCsvImportRoundTrip::test_export_then_import_reproduces_data` | 0.445 |
| [pass] | `tests.test_smoke.TestCsvImportRoundTrip::test_invalid_dates_dont_crash` | 0.242 |
| [pass] | `tests.test_smoke.TestCsvImportRoundTrip::test_missing_csv_files_are_skipped` | 0.209 |
| [pass] | `tests.test_smoke.TestDayStructurePersistence::test_entry_persists` | 0.194 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_caps_are_destructive` | 0.181 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_contract_round_trip` | 0.200 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_member_keeps_orphan_contracts` | 0.198 |
| [pass] | `tests.test_smoke.TestDeleteCapabilities::test_delete_unknown_returns_error` | 0.178 |
| [pass] | `tests.test_smoke.TestDestructiveFlags::test_critical_capabilities_are_marked` | 0.169 |
| [pass] | `tests.test_smoke.TestDiagnose::test_collect_returns_expected_shape` | 1.051 |
| [pass] | `tests.test_smoke.TestDisabledModuleSurfaced::test_disabled_contracts_yields_warning_in_finance_events` | 0.190 |
| [pass] | `tests.test_smoke.TestEncryption::test_encryption_requires_sqlcipher3` | 0.003 |
| [pass] | `tests.test_smoke.TestEncryption::test_plain_mode_when_no_key` | 0.197 |
| [pass] | `tests.test_smoke.TestGeminiAssistantStub::test_mode_reports_llm` | 0.261 |
| [pass] | `tests.test_smoke.TestGeminiAssistantStub::test_token_usage_accumulates` | 0.204 |
| [pass] | `tests.test_smoke.TestHasCapabilityHonorsDisabled::test_has_capability_false_when_disabled` | 0.162 |
| [pass] | `tests.test_smoke.TestHasCapabilityHonorsDisabled::test_has_capability_returns_after_enable` | 0.162 |
| [pass] | `tests.test_smoke.TestHttpSyncRoundTrip::test_http_provider_append_and_fetch` | 0.525 |
| [pass] | `tests.test_smoke.TestI18n::test_default_german` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_en_missing_key_falls_back_to_de` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_english_translation` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_missing_key_returns_key` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_missing_key_with_default` | 0.001 |
| [pass] | `tests.test_smoke.TestI18n::test_unknown_language_falls_back_to_default` | 0.001 |
| [pass] | `tests.test_smoke.TestIcalExport::test_export_creates_valid_ical` | 0.187 |
| [pass] | `tests.test_smoke.TestIcalImportRoundTrip::test_import_missing_file_returns_error` | 0.199 |
| [pass] | `tests.test_smoke.TestIcalImportRoundTrip::test_roundtrip` | 0.371 |
| [pass] | `tests.test_smoke.TestInboxExtractText::test_empty_payload_returns_empty_string` | 0.001 |
| [pass] | `tests.test_smoke.TestInboxExtractText::test_multipart_without_textplain_returns_empty` | 0.001 |
| [pass] | `tests.test_smoke.TestInputValidation::test_calendar_unknown_category_normalizes` | 0.204 |
| [pass] | `tests.test_smoke.TestInputValidation::test_family_task_rejects_zero_interval` | 0.245 |
| [pass] | `tests.test_smoke.TestInputValidation::test_finance_rejects_bad_date` | 0.169 |
| [pass] | `tests.test_smoke.TestInputValidation::test_finance_rejects_negative_amount` | 0.155 |
| [pass] | `tests.test_smoke.TestInputValidation::test_social_rejects_empty_name` | 0.168 |
| [pass] | `tests.test_smoke.TestInputValidation::test_social_rejects_non_positive_cadence` | 0.161 |
| [pass] | `tests.test_smoke.TestLamportCrdt::test_clock_ticks_monotonically` | 0.001 |
| [pass] | `tests.test_smoke.TestLamportCrdt::test_events_get_lamport_counter` | 0.200 |
| [pass] | `tests.test_smoke.TestLamportCrdt::test_replay_order_uses_lamport` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_apply_token_rejects_empty` | 0.206 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_apply_token_rejects_garbage` | 0.162 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_apply_token_round_trip` | 0.182 |
| [pass] | `tests.test_smoke.TestLicensing::test_action_start_trial_success_then_blocked` | 0.177 |
| [pass] | `tests.test_smoke.TestLicensing::test_activate_pro_sets_year_for_annual` | 0.221 |
| [pass] | `tests.test_smoke.TestLicensing::test_activation_rejects_free_tier` | 0.196 |
| [pass] | `tests.test_smoke.TestLicensing::test_activation_requires_withdrawal_waiver` | 0.207 |
| [pass] | `tests.test_smoke.TestLicensing::test_affiliate_block_empty_when_no_partners` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_affiliate_block_format` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_affiliate_block_in_letter_text_is_static` | 0.194 |
| [pass] | `tests.test_smoke.TestLicensing::test_all_quotes_returns_pricing_tiers` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_annual_applies_20_percent_discount` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_annual_savings_vs_monthly` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_annual_total_matches_readme_base_tier` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_apply_token_persists_token_string` | 0.230 |
| [pass] | `tests.test_smoke.TestLicensing::test_build_pricing_rows_marks_recommended` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_build_pricing_rows_skips_family_above_cap` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_cancellation_includes_affiliate_suggestions` | 0.204 |
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
| [pass] | `tests.test_smoke.TestLicensing::test_grandfathered_keeps_read_but_blocks_write` | 0.215 |
| [pass] | `tests.test_smoke.TestLicensing::test_grandfathering_migration_runs_once` | 0.307 |
| [pass] | `tests.test_smoke.TestLicensing::test_grandfathering_skipped_for_empty_db` | 0.186 |
| [pass] | `tests.test_smoke.TestLicensing::test_invalid_persons_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_issuer_signs_token_and_sends_mail` | 0.009 |
| [pass] | `tests.test_smoke.TestLicensing::test_issuer_skips_cancellations` | 0.002 |
| [pass] | `tests.test_smoke.TestLicensing::test_lemon_signature_and_parse` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_lemon_uninteresting_event_returns_none` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_license_round_trip` | 0.199 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_defaults_to_free` | 0.183 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_drops_tampered_token` | 0.195 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_handles_corrupt_values` | 0.202 |
| [pass] | `tests.test_smoke.TestLicensing::test_load_license_keeps_expired_token_for_grace` | 0.202 |
| [pass] | `tests.test_smoke.TestLicensing::test_mobile_pricing_has_markup` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_monthly_base_two_persons` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_monthly_charges_extra_persons` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_paddle_parse_event` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_paddle_signature_round_trip` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_paddle_unknown_price_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_pricing_onboarded_flag_persists` | 0.202 |
| [pass] | `tests.test_smoke.TestLicensing::test_pro_downgrades_after_grace_period` | 0.316 |
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
| [pass] | `tests.test_smoke.TestLicensing::test_token_rejects_expired` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_rejects_tampered_payload` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_sign_verify_round_trip` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_token_without_configured_pubkey_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestLicensing::test_trial_is_not_reusable` | 0.206 |
| [pass] | `tests.test_smoke.TestLicensing::test_trial_starts_and_expires` | 0.209 |
| [pass] | `tests.test_smoke.TestLicensing::test_webhook_server_end_to_end` | 0.517 |
| [pass] | `tests.test_smoke.TestLicensing::test_webhook_server_rejects_bad_signature` | 0.504 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_fenced_json` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_fenced_without_lang` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_invalid_returns_empty` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_plain_json` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmJsonParsing::test_prose_with_embedded_json` | 0.001 |
| [pass] | `tests.test_smoke.TestLlmProposalValidation::test_missing_required_dropped` | 0.161 |
| [pass] | `tests.test_smoke.TestLlmProposalValidation::test_unknown_target_capability_dropped` | 0.166 |
| [pass] | `tests.test_smoke.TestModuleStatePersistence::test_disabled_module_id_persists` | 0.200 |
| [pass] | `tests.test_smoke.TestNotesModule::test_add_list_update_attach_delete` | 0.195 |
| [pass] | `tests.test_smoke.TestNotesModule::test_empty_title_rejected` | 0.186 |
| [pass] | `tests.test_smoke.TestNotesModule::test_invalid_entity_type_rejected` | 0.195 |
| [pass] | `tests.test_smoke.TestNotesModule::test_search_finds_notes` | 0.207 |
| [pass] | `tests.test_smoke.TestPrintFileNoShell::test_missing_file_returns_error` | 0.001 |
| [pass] | `tests.test_smoke.TestPrintFileNoShell::test_path_with_spaces_handled` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_db_path_default` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_db_path_with_profile` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_explicit_overrides_env` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_resolve_profile_uses_env` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_sanitize_profile` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_state_dir_default_and_profile` | 0.001 |
| [pass] | `tests.test_smoke.TestProfile::test_two_profiles_use_separate_files` | 0.405 |
| [pass] | `tests.test_smoke.TestProposalUpdate::test_update_blocked_after_accept` | 0.195 |
| [pass] | `tests.test_smoke.TestProposalUpdate::test_update_payload_replaces_value` | 0.199 |
| [pass] | `tests.test_smoke.TestProposalUpdate::test_update_then_accept_uses_new_payload` | 0.179 |
| [pass] | `tests.test_smoke.TestProposalsFlow::test_price_change_round_trip` | 0.225 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_invalid_date_rejected` | 0.189 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_negative_recurrence_rejected` | 0.192 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_none_recurrence_ok` | 0.190 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_positive_recurrence_ok` | 0.175 |
| [pass] | `tests.test_smoke.TestRecurrenceValidation::test_zero_recurrence_rejected` | 0.159 |
| [pass] | `tests.test_smoke.TestRegistry::test_capabilities_registered` | 0.160 |
| [pass] | `tests.test_smoke.TestRegistry::test_module_to_module_via_context` | 0.147 |
| [pass] | `tests.test_smoke.TestRegistry::test_unknown_capability_returns_error` | 0.152 |
| [pass] | `tests.test_smoke.TestRegistryGetCapability::test_returns_capability_object` | 0.166 |
| [pass] | `tests.test_smoke.TestRegistryGetCapability::test_returns_none_for_disabled_module` | 0.152 |
| [pass] | `tests.test_smoke.TestRegistryGetCapability::test_returns_none_for_unknown` | 0.197 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_assistant_ask_lock_serializes` | 0.202 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_bulk_complete_overdue_dispatches_individual_tasks` | 0.226 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_bulk_delete_archived_uses_repository_method` | 0.205 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_deleting_contract_cleans_attached_notes` | 0.221 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_geometry_validation` | 0.187 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_http_provider_has_read_all` | 4.285 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_export_folds_at_byte_boundary` | 0.245 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_import_rejects_nonexistent` | 0.240 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_import_rejects_path_outside_or_bad_extension` | 0.193 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_ical_import_validates_recurrence` | 0.206 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_initial_lamport_ignores_other_devices` | 0.192 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_internal_capabilities_hidden_from_llm` | 0.155 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_notes_entity_id_zero_preserved` | 0.144 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_rrule_uses_yearly_for_365` | 0.168 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_sync_event_args_deep_copy` | 0.160 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_unescape_preserves_real_null_bytes` | 0.159 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_vcard_import_clamps_cadence` | 0.171 |
| [pass] | `tests.test_smoke.TestReviewFixes::test_vcard_import_rejects_too_large` | 0.209 |
| [pass] | `tests.test_smoke.TestSearch::test_no_hit` | 0.211 |
| [pass] | `tests.test_smoke.TestSearch::test_search_finds_multiple_sources` | 0.204 |
| [pass] | `tests.test_smoke.TestSearch::test_short_query_rejected` | 0.185 |
| [pass] | `tests.test_smoke.TestSettings::test_db_value_overrides_default` | 0.149 |
| [pass] | `tests.test_smoke.TestSettings::test_defaults_when_empty` | 0.172 |
| [pass] | `tests.test_smoke.TestSettings::test_env_overrides_db` | 0.162 |
| [pass] | `tests.test_smoke.TestSettings::test_secret_is_not_persisted` | 0.164 |
| [pass] | `tests.test_smoke.TestSmtpWiring::test_smtp_config_from_app_config` | 0.001 |
| [pass] | `tests.test_smoke.TestSqlCipherValidation::test_nul_byte_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestSqlCipherValidation::test_too_short_rejected` | 0.001 |
| [pass] | `tests.test_smoke.TestStatistics::test_contracts_overview_top_3` | 0.228 |
| [pass] | `tests.test_smoke.TestStatistics::test_expenses_per_category_aggregates` | 0.184 |
| [pass] | `tests.test_smoke.TestStatistics::test_expenses_per_month_returns_buckets` | 0.195 |
| [pass] | `tests.test_smoke.TestStatistics::test_rejects_zero_months` | 0.200 |
| [pass] | `tests.test_smoke.TestStatistics::test_yearly_summary` | 0.234 |
| [pass] | `tests.test_smoke.TestSyncCompaction::test_compact_drops_oldest` | 0.032 |
| [pass] | `tests.test_smoke.TestSyncExpandedCapabilities::test_contract_replays_on_other_device` | 0.358 |
| [pass] | `tests.test_smoke.TestSyncReentry::test_non_synced_outer_lets_nested_log` | 0.200 |
| [pass] | `tests.test_smoke.TestSyncReentry::test_synced_outer_suppresses_synced_nested` | 0.193 |
| [pass] | `tests.test_smoke.TestSyncServerCompaction::test_server_drops_oldest_when_over_limit` | 0.571 |
| [pass] | `tests.test_smoke.TestSyncServerTls::test_serve_with_bad_cert_path_raises` | 0.003 |
| [pass] | `tests.test_smoke.TestThreadSafety::test_concurrent_dispatch` | 0.699 |
| [pass] | `tests.test_smoke.TestUtcTimestamps::test_event_timestamp_has_utc_marker` | 0.178 |
| [pass] | `tests.test_smoke.TestUtcTimestampsInDb::test_assistant_log_uses_utc` | 0.195 |
| [pass] | `tests.test_smoke.TestUtcTimestampsInDb::test_contract_created_at_uses_utc` | 0.202 |
| [pass] | `tests.test_smoke.TestVCardExport::test_export_creates_valid_vcard` | 0.194 |
| [pass] | `tests.test_smoke.TestVCardImportRoundTrip::test_roundtrip_preserves_rhythmus` | 0.353 |
| [pass] | `tests.test_smoke.TestYearlyPdfReport::test_pdf_report_produced` | 0.199 |
| [pass] | `tests.test_store_listing.TestCuratedQuality::test_all_curated_within_limits` | 0.001 |
| [pass] | `tests.test_store_listing.TestGenerateLocalizations::test_does_not_overwrite_existing` | 0.001 |
| [pass] | `tests.test_store_listing.TestGenerateLocalizations::test_generated_is_valid` | 0.001 |
| [pass] | `tests.test_store_listing.TestGenerateLocalizations::test_merges_curated_into_base` | 0.001 |
| [pass] | `tests.test_store_listing.TestRealRepo::test_real_has_major_languages` | 0.011 |
| [pass] | `tests.test_store_listing.TestRealRepo::test_real_localizations_valid` | 0.011 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_clean_curated_passes` | 0.001 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_empty_is_error` | 0.001 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_limits_match_play` | 0.001 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_missing_field_is_error` | 0.001 |
| [pass] | `tests.test_store_listing.TestValidateLocalizations::test_too_long_title_is_error` | 0.001 |
| [skip] | `tests.test_integration.TestGeminiRealApi::test_simple_ask_returns_text` | 0.001 |
| [skip] | `tests.test_integration.TestSqlCipherRealRoundTrip::test_encrypt_write_close_reopen` | 0.005 |
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

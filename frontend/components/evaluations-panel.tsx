"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Beaker, Bot, Bug, ListChecks, Play, RefreshCw, RotateCcw, Save, ShieldAlert, Trash2 } from "lucide-react";

import { useToast } from "@/components/toast-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { HoverHint } from "@/components/ui/hover-hint";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  createEvalCase,
  deleteEvalCase,
  getApiErrorMessage,
  getEvalCases,
  getEvalProfile,
  getEvalRun,
  getEvalRunStatus,
  listEvalRuns,
  listOllamaModels,
  startEvalRun,
  updateEvalCase,
  updateEvalProfile,
} from "@/lib/api";
import type { EvalCase, EvalProvider, EvalRunDetail, EvalRunSummary, EvalRunType } from "@/lib/types";

const RUN_TYPE_ITEMS = [
  { label: "Full Suite", value: "full" },
  { label: "Retrieval Only", value: "retrieval" },
  { label: "Answer Only", value: "answer" },
  { label: "Red-Team Only", value: "redteam" },
];

const CASE_TYPE_ITEMS = [
  { label: "All", value: "all" },
  { label: "Retrieval", value: "retrieval" },
  { label: "Answer", value: "answer" },
  { label: "Red-Team", value: "redteam" },
];

function parseLines(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function EvaluationsPanel({ folderName }: { folderName: string }) {
  const queryClient = useQueryClient();
  const { pushToast } = useToast();
  const [provider, setProvider] = useState<EvalProvider>("ollama");
  const [modelName, setModelName] = useState("");
  const [autoRunEnabled, setAutoRunEnabled] = useState(false);
  const [rememberOpenAiKey, setRememberOpenAiKey] = useState(false);
  const [openAiKey, setOpenAiKey] = useState("");
  const [openAiModel, setOpenAiModel] = useState("");
  const [runType, setRunType] = useState<EvalRunType>("full");
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [editingCaseId, setEditingCaseId] = useState<string | null>(null);
  const [caseName, setCaseName] = useState("");
  const [caseQuestion, setCaseQuestion] = useState("");
  const [referenceAnswer, setReferenceAnswer] = useState("");
  const [expectedPoints, setExpectedPoints] = useState("");
  const [expectedSources, setExpectedSources] = useState("");
  const [tags, setTags] = useState("");
  const [caseType, setCaseType] = useState<EvalCase["case_type"]>("all");
  const [caseEnabled, setCaseEnabled] = useState(true);

  const openAiKeyStorageKey = `vecseek:${folderName}:openai_api_key`;
  const openAiModelStorageKey = `vecseek:${folderName}:openai_model_name`;

  const profileQuery = useQuery({
    queryKey: ["eval-profile", folderName],
    queryFn: () => getEvalProfile(folderName),
  });
  const casesQuery = useQuery({
    queryKey: ["eval-cases", folderName],
    queryFn: () => getEvalCases(folderName),
  });
  const runsQuery = useQuery({
    queryKey: ["eval-runs", folderName],
    queryFn: () => listEvalRuns(folderName),
    refetchInterval: (query) =>
      (query.state.data ?? []).some((run) => run.status === "pending" || run.status === "running") ? 2500 : false,
  });
  const ollamaModelsQuery = useQuery({
    queryKey: ["ollama-models"],
    queryFn: listOllamaModels,
    enabled: provider === "ollama",
  });
  const runDetailQuery = useQuery({
    queryKey: ["eval-run", folderName, selectedRunId],
    queryFn: () => getEvalRun(folderName, selectedRunId),
    enabled: !!selectedRunId,
    refetchInterval: (query) =>
      query.state.data && (query.state.data.status === "pending" || query.state.data.status === "running") ? 2500 : false,
  });

  useEffect(() => {
    const storedModel = window.localStorage.getItem(openAiModelStorageKey) ?? "";
    const storedKey = window.localStorage.getItem(openAiKeyStorageKey) ?? "";
    setOpenAiModel(storedModel);
    setOpenAiKey(storedKey);
    setRememberOpenAiKey(Boolean(storedKey));
  }, [openAiKeyStorageKey, openAiModelStorageKey]);

  useEffect(() => {
    if (profileQuery.data) {
      setProvider(profileQuery.data.provider);
      setModelName(profileQuery.data.model_name);
      setAutoRunEnabled(profileQuery.data.auto_run_enabled);
    }
  }, [profileQuery.data]);

  useEffect(() => {
    window.localStorage.setItem(openAiModelStorageKey, openAiModel);
  }, [openAiModel, openAiModelStorageKey]);

  useEffect(() => {
    if (rememberOpenAiKey && openAiKey) {
      window.localStorage.setItem(openAiKeyStorageKey, openAiKey);
    } else {
      window.localStorage.removeItem(openAiKeyStorageKey);
    }
  }, [rememberOpenAiKey, openAiKey, openAiKeyStorageKey]);

  useEffect(() => {
    if (!selectedRunId && runsQuery.data?.length) {
      setSelectedRunId(runsQuery.data[0].id);
    }
  }, [runsQuery.data, selectedRunId]);

  const saveProfileMutation = useMutation({
    mutationFn: () =>
      updateEvalProfile(folderName, {
        provider,
        model_name: provider === "openai" ? openAiModel.trim() : modelName.trim(),
        auto_run_enabled: autoRunEnabled,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["eval-profile", folderName] });
      pushToast({ tone: "success", title: "Evaluation profile saved", description: "Provider and model settings were updated." });
    },
    onError: (error: unknown) =>
      pushToast({ tone: "error", title: "Profile save failed", description: getApiErrorMessage(error) }),
  });

  const runMutation = useMutation({
    mutationFn: () =>
      startEvalRun(folderName, {
        run_type: runType,
        provider,
        model_name: provider === "openai" ? openAiModel.trim() : modelName.trim(),
        openai_api_key: provider === "openai" ? openAiKey.trim() : undefined,
      }),
    onSuccess: async (run) => {
      setSelectedRunId(run.id);
      await queryClient.invalidateQueries({ queryKey: ["eval-runs", folderName] });
      pushToast({ tone: "success", title: "Evaluation started", description: "VecSeek queued the selected evaluation suite." });
    },
    onError: (error: unknown) =>
      pushToast({ tone: "error", title: "Evaluation failed to start", description: getApiErrorMessage(error) }),
  });

  const caseMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        name: caseName,
        question: caseQuestion,
        reference_answer: referenceAnswer || undefined,
        expected_answer_points: parseLines(expectedPoints),
        expected_source_files: parseLines(expectedSources),
        tags: parseLines(tags),
        case_type: caseType,
        enabled: caseEnabled,
      };
      if (editingCaseId) {
        return updateEvalCase(folderName, editingCaseId, payload);
      }
      return createEvalCase(folderName, payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["eval-cases", folderName] });
      setEditingCaseId(null);
      setCaseName("");
      setCaseQuestion("");
      setReferenceAnswer("");
      setExpectedPoints("");
      setExpectedSources("");
      setTags("");
      setCaseType("all");
      setCaseEnabled(true);
      pushToast({ tone: "success", title: "Evaluation case saved", description: "The folder eval dataset was updated." });
    },
    onError: (error: unknown) =>
      pushToast({ tone: "error", title: "Case save failed", description: getApiErrorMessage(error) }),
  });

  const deleteCaseMutation = useMutation({
    mutationFn: (caseId: string) => deleteEvalCase(folderName, caseId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["eval-cases", folderName] });
      pushToast({ tone: "success", title: "Evaluation case deleted", description: "The case was removed from this folder." });
    },
    onError: (error: unknown) =>
      pushToast({ tone: "error", title: "Delete failed", description: getApiErrorMessage(error) }),
  });

  const currentRun = runDetailQuery.data;
  const ollamaModelsError = provider === "ollama" && ollamaModelsQuery.error ? getApiErrorMessage(ollamaModelsQuery.error) : "";
  const hasOllamaModels = (ollamaModelsQuery.data ?? []).length > 0;
  const trendSummary = useMemo(() => {
    const runs = runsQuery.data ?? [];
    if (!runs.length) {
      return null;
    }
    const latest = runs[0];
    const previous = runs.find((item) => item.id === latest.previous_run_id);
    return {
      latest,
      previous,
    };
  }, [runsQuery.data]);

  const fillCaseForm = (item: EvalCase) => {
    setEditingCaseId(item.id);
    setCaseName(item.name);
    setCaseQuestion(item.question);
    setReferenceAnswer(item.reference_answer ?? "");
    setExpectedPoints(item.expected_answer_points.join("\n"));
    setExpectedSources(item.expected_source_files.join("\n"));
    setTags(item.tags.join("\n"));
    setCaseType(item.case_type);
    setCaseEnabled(item.enabled);
  };

  return (
    <Card className="p-5 sm:p-6">
      <div className="grid gap-5">
        <div className="grid gap-5 xl:grid-cols-[0.92fr,1.08fr]">
          <div>
            <HoverHint hint="Every folder can now carry its own evaluation suite, model choice, and run history.">
              <div>
                <p className="section-label">Evaluations</p>
                <p className="mt-3 font-display text-[2.15rem] leading-none text-text">Trust the folder, not just the demo</p>
                <p className="mt-3 text-sm leading-6 text-muted">
                  Configure the eval provider, build a gold dataset, and track retrieval, answer, and red-team quality over time.
                </p>
              </div>
            </HoverHint>
            <div className="mt-6 flex h-11 w-11 items-center justify-center rounded-2xl bg-card-secondary text-accent">
              <Beaker className="h-5 w-5" />
            </div>
          </div>

          <div className="rounded-[28px] border border-black/[0.06] bg-card-secondary/35 p-5 dark:border-white/10">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-medium text-text">Provider</label>
                <Select
                  value={provider}
                  onValueChange={(value) => setProvider(value as EvalProvider)}
                  placeholder="Choose provider"
                  items={[
                    { label: "Ollama", value: "ollama" },
                    { label: "OpenAI", value: "openai" },
                  ]}
                />
              </div>

              {provider === "ollama" ? (
                <div>
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <label className="block text-sm font-medium text-text">Ollama model</label>
                    <Button
                      type="button"
                      variant="ghost"
                      className="h-9 rounded-xl px-3"
                      onClick={() => void ollamaModelsQuery.refetch()}
                      disabled={ollamaModelsQuery.isFetching}
                    >
                      <RefreshCw className={`mr-2 h-4 w-4 ${ollamaModelsQuery.isFetching ? "animate-spin" : ""}`} />
                      Refresh
                    </Button>
                  </div>
                  {hasOllamaModels ? (
                    <Select
                      value={modelName}
                      onValueChange={setModelName}
                      placeholder="Select a downloaded Ollama model"
                      items={(ollamaModelsQuery.data ?? []).map((model) => ({ label: model.name, value: model.name }))}
                    />
                  ) : (
                    <Input
                      value={modelName}
                      onChange={(event) => setModelName(event.target.value)}
                      placeholder={ollamaModelsQuery.isLoading ? "Loading Ollama models..." : "Type an Ollama model name"}
                    />
                  )}
                  {ollamaModelsError ? (
                    <p className="mt-2 text-sm leading-6 text-danger">{ollamaModelsError}</p>
                  ) : null}
                  {!ollamaModelsError && !ollamaModelsQuery.isLoading && !(ollamaModelsQuery.data ?? []).length ? (
                    <p className="mt-2 text-sm leading-6 text-muted">
                      No downloaded Ollama models were found yet. Pull a model in Ollama, or type the exact model name manually.
                    </p>
                  ) : null}
                </div>
              ) : (
                <>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-text">OpenAI model</label>
                    <Input value={openAiModel} onChange={(event) => setOpenAiModel(event.target.value)} placeholder="gpt-4.1-mini" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="mb-2 block text-sm font-medium text-text">OpenAI API key</label>
                    <Input type="password" value={openAiKey} onChange={(event) => setOpenAiKey(event.target.value)} placeholder="sk-..." />
                    <p className="mt-2 text-sm leading-6 text-muted">
                      OpenAI evaluations need internet access from this machine. The API key stays in this browser unless you remove it.
                    </p>
                    <label className="mt-3 flex items-center gap-3 text-sm text-muted">
                      <input type="checkbox" checked={rememberOpenAiKey} onChange={(event) => setRememberOpenAiKey(event.target.checked)} />
                      Remember this API key in this browser
                    </label>
                  </div>
                </>
              )}

              <label className="flex items-center justify-between rounded-[22px] border border-black/[0.06] bg-card px-4 py-3 text-sm text-text dark:border-white/10 md:col-span-2">
                <span>Auto-run evaluations after a successful re-index</span>
                <input type="checkbox" checked={autoRunEnabled} onChange={(event) => setAutoRunEnabled(event.target.checked)} />
              </label>
            </div>

            <div className="mt-5 flex justify-end">
              <Button disabled={saveProfileMutation.isPending} onClick={() => saveProfileMutation.mutate()}>
                <Save className="mr-2 h-4 w-4" />
                {saveProfileMutation.isPending ? "Saving..." : "Save profile"}
              </Button>
            </div>
          </div>
        </div>

        <div className="grid gap-5 xl:grid-cols-[1.02fr,0.98fr]">
          <div className="rounded-[28px] border border-black/[0.06] bg-card p-5 dark:border-white/10">
            <div className="flex items-center justify-between gap-3 border-b border-black/[0.06] pb-4 dark:border-white/10">
              <div>
                <p className="section-label">Eval Dataset</p>
                <p className="mt-2 text-sm leading-6 text-muted">Create reusable gold cases for retrieval, answer, or red-team testing.</p>
              </div>
              <ListChecks className="h-5 w-5 text-accent" />
            </div>

            <div className="mt-4 grid gap-4">
              <Input value={caseName} onChange={(event) => setCaseName(event.target.value)} placeholder="Case name" />
              <Textarea value={caseQuestion} onChange={(event) => setCaseQuestion(event.target.value)} placeholder="Question or adversarial prompt" className="min-h-24" />
              <Textarea value={referenceAnswer} onChange={(event) => setReferenceAnswer(event.target.value)} placeholder="Reference answer (optional)" className="min-h-24" />
              <Textarea value={expectedPoints} onChange={(event) => setExpectedPoints(event.target.value)} placeholder="Expected answer points, one per line" className="min-h-24" />
              <Textarea value={expectedSources} onChange={(event) => setExpectedSources(event.target.value)} placeholder="Expected source file names, one per line" className="min-h-24" />
              <Textarea value={tags} onChange={(event) => setTags(event.target.value)} placeholder="Tags, one per line" className="min-h-20" />
              <div className="grid gap-4 md:grid-cols-2">
                <Select value={caseType} onValueChange={(value) => setCaseType(value as EvalCase["case_type"])} placeholder="Case type" items={CASE_TYPE_ITEMS} />
                <label className="flex items-center justify-between rounded-[22px] border border-black/[0.06] bg-card px-4 py-3 text-sm text-text dark:border-white/10">
                  <span>Enabled</span>
                  <input type="checkbox" checked={caseEnabled} onChange={(event) => setCaseEnabled(event.target.checked)} />
                </label>
              </div>

              <div className="flex flex-wrap justify-end gap-3">
                {editingCaseId ? (
                  <Button variant="secondary" onClick={() => {
                    setEditingCaseId(null);
                    setCaseName("");
                    setCaseQuestion("");
                    setReferenceAnswer("");
                    setExpectedPoints("");
                    setExpectedSources("");
                    setTags("");
                    setCaseType("all");
                    setCaseEnabled(true);
                  }}>
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Reset
                  </Button>
                ) : null}
                <Button disabled={caseMutation.isPending} onClick={() => caseMutation.mutate()}>
                  {caseMutation.isPending ? "Saving..." : editingCaseId ? "Update case" : "Add case"}
                </Button>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              {(casesQuery.data ?? []).map((item) => (
                <div key={item.id} className="rounded-[22px] border border-black/[0.06] bg-card-secondary/35 p-4 dark:border-white/10">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-text">{item.name}</p>
                      <p className="mt-2 text-sm leading-6 text-muted">{item.question}</p>
                      <p className="mt-3 text-[11px] uppercase tracking-[0.2em] text-muted">
                        {item.case_type} · {item.enabled ? "enabled" : "disabled"}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="secondary" onClick={() => fillCaseForm(item)}>Edit</Button>
                      <Button variant="danger" onClick={() => deleteCaseMutation.mutate(item.id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
              {!casesQuery.data?.length ? (
                <div className="rounded-[24px] border border-dashed border-black/[0.08] bg-card px-4 py-8 text-sm text-muted dark:border-white/10">
                  No evaluation cases yet.
                </div>
              ) : null}
            </div>
          </div>

          <div className="grid gap-5">
            <div className="rounded-[28px] border border-black/[0.06] bg-card p-5 dark:border-white/10">
              <div className="flex items-center justify-between gap-3 border-b border-black/[0.06] pb-4 dark:border-white/10">
                <div>
                  <p className="section-label">Run Suite</p>
                  <p className="mt-2 text-sm leading-6 text-muted">Launch retrieval, answer, red-team, or full evaluation runs.</p>
                </div>
                <Play className="h-5 w-5 text-accent" />
              </div>
              <div className="mt-4 grid gap-4">
                <Select value={runType} onValueChange={(value) => setRunType(value as EvalRunType)} placeholder="Select run type" items={RUN_TYPE_ITEMS} />
                <div className="flex justify-end">
                  <Button disabled={runMutation.isPending} onClick={() => runMutation.mutate()}>
                    <Play className="mr-2 h-4 w-4" />
                    {runMutation.isPending ? "Starting..." : "Run evaluations"}
                  </Button>
                </div>
              </div>
            </div>

            <div className="rounded-[28px] border border-black/[0.06] bg-card p-5 dark:border-white/10">
              <div className="flex items-center justify-between gap-3 border-b border-black/[0.06] pb-4 dark:border-white/10">
                <div>
                  <p className="section-label">History</p>
                  <p className="mt-2 text-sm leading-6 text-muted">Track each run, compare drift, and inspect failures.</p>
                </div>
                <ShieldAlert className="h-5 w-5 text-accent" />
              </div>

              {trendSummary ? (
                <div className="mt-4 rounded-[22px] bg-card-secondary/35 p-4 text-sm text-muted">
                  Latest overall score: {Number(trendSummary.latest.summary_metrics?.overall_average ?? 0).toFixed(3)}
                  {trendSummary.previous ? (
                    <span> · Previous {Number(trendSummary.previous.summary_metrics?.overall_average ?? 0).toFixed(3)}</span>
                  ) : null}
                </div>
              ) : null}

              <div className="mt-4 space-y-3">
                {(runsQuery.data ?? []).map((run) => (
                  <button
                    key={run.id}
                    className={`w-full rounded-[22px] border px-4 py-3 text-left transition ${selectedRunId === run.id ? "border-accent bg-card-secondary/45" : "border-black/[0.06] bg-card dark:border-white/10"}`}
                    onClick={() => setSelectedRunId(run.id)}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-text">{run.run_type} · {run.status}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-muted">{run.provider} · {run.model_name || "no model selected"}</p>
                      </div>
                      <span className="text-xs text-muted">{new Date(run.started_at).toLocaleString()}</span>
                    </div>
                  </button>
                ))}
                {!runsQuery.data?.length ? (
                  <div className="rounded-[24px] border border-dashed border-black/[0.08] bg-card px-4 py-8 text-sm text-muted dark:border-white/10">
                    No evaluation runs yet.
                  </div>
                ) : null}
              </div>
            </div>

            <div className="rounded-[28px] border border-black/[0.06] bg-card p-5 dark:border-white/10">
              <div className="flex items-center justify-between gap-3 border-b border-black/[0.06] pb-4 dark:border-white/10">
                <div>
                  <p className="section-label">Run Detail</p>
                  <p className="mt-2 text-sm leading-6 text-muted">See metric-level outcomes, misses, and red-team notes.</p>
                </div>
                <Bot className="h-5 w-5 text-accent" />
              </div>
              {currentRun ? (
                <div className="mt-4 space-y-4">
                  <div className="rounded-[22px] bg-card-secondary/35 p-4 text-sm text-muted">
                    Overall {Number(currentRun.summary_metrics?.overall_average ?? 0).toFixed(3)} · Retrieval {Number(currentRun.summary_metrics?.retrieval_average ?? 0).toFixed(3)} · Answer {Number(currentRun.summary_metrics?.answer_average ?? 0).toFixed(3)} · Red-team {Number(currentRun.summary_metrics?.redteam_average ?? 0).toFixed(3)}
                    {currentRun.error_message ? <p className="mt-2 text-danger">{currentRun.error_message}</p> : null}
                  </div>

                  {currentRun.items.map((item) => (
                    <div key={item.id} className="rounded-[22px] border border-black/[0.06] bg-card-secondary/35 p-4 dark:border-white/10">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-text">{item.eval_type}</p>
                        <span className="text-xs uppercase tracking-[0.18em] text-muted">
                          {item.passed ? "pass" : "fail"} · {Number(item.score ?? 0).toFixed(3)}
                        </span>
                      </div>
                      <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-6 text-muted">
                        {JSON.stringify(item.details, null, 2)}
                      </pre>
                    </div>
                  ))}

                  {currentRun.artifacts.map((artifact) => (
                    <div key={artifact.id} className="rounded-[22px] border border-black/[0.06] bg-card p-4 dark:border-white/10">
                      <div className="flex items-center gap-3">
                        <Bug className="h-4 w-4 text-accent" />
                        <p className="text-sm font-semibold text-text">{artifact.name}</p>
                      </div>
                      <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-6 text-muted">{artifact.content}</pre>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-4 rounded-[24px] border border-dashed border-black/[0.08] bg-card px-4 py-8 text-sm text-muted dark:border-white/10">
                  Select a run to inspect its details.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

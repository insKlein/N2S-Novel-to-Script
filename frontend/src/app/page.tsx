"use client";

import { useMemo, useState } from "react";
import {
  CheckCircle2,
  Clipboard,
  Download,
  FileText,
  Loader2,
  Play,
  RefreshCw,
  Upload,
} from "lucide-react";

type Episode = {
  episode: number;
  path: string;
  yaml: string;
};

type ProjectPayload = {
  title: string;
  project_dir: string;
  episodes: Episode[];
  reports: Record<string, string>;
};

const API_BASE = process.env.NEXT_PUBLIC_N2S_API_URL ?? "http://127.0.0.1:8000";

const SAMPLE_NOVEL = `第一章 雨夜

林遥站在旧楼门口，手里攥着一张被雨水打湿的诊断单。电话那头，母亲的声音很轻，却像石头一样压下来。

“你妹妹的手术费，家里只能靠你了。”

第二章 合同

第二天清晨，林遥走进公司会议室。桌上摆着一份转让协议，经理把笔推到她面前。

“签了吧。项目算公司的，你别闹得太难看。”

第三章 录音

她没有接那支笔，只从包里拿出一支录音笔，放在会议桌中央。

播放键按下，经理昨晚的声音清清楚楚传出来：“方案是她做的，但署名必须换成我。”`;

const reportTabs = [
  ["analysis", "分析"],
  ["planning", "规划"],
  ["characters", "角色"],
  ["insight", "洞察"],
  ["emotion", "情绪"],
  ["final_check", "终检"],
] as const;

export default function Home() {
  const [title, setTitle] = useState("示例剧本");
  const [episodes, setEpisodes] = useState(3);
  const [mock, setMock] = useState(true);
  const [novelText, setNovelText] = useState(SAMPLE_NOVEL);
  const [activeEpisode, setActiveEpisode] = useState(1);
  const [activeReport, setActiveReport] = useState<(typeof reportTabs)[number][0]>("analysis");
  const [project, setProject] = useState<ProjectPayload | null>(null);
  const [status, setStatus] = useState("等待输入");
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");
  const [isRunning, setIsRunning] = useState(false);

  const currentEpisode = useMemo(
    () => project?.episodes.find((item) => item.episode === activeEpisode) ?? project?.episodes[0],
    [activeEpisode, project],
  );

  async function convertNovel() {
    setIsRunning(true);
    setError("");
    setStatus("分析中");
    try {
      const response = await fetch(`${API_BASE}/api/convert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          novel_text: novelText,
          episodes,
          mock,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "转换失败");
      }
      setProject(data);
      setActiveEpisode(data.episodes[0]?.episode ?? 1);
      setStatus("完成");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "转换失败");
      setStatus("失败");
    } finally {
      setIsRunning(false);
    }
  }

  async function importNovelFile(file: File | undefined) {
    if (!file) return;
    const extension = file.name.toLowerCase().split(".").pop();
    if (!extension || !["txt", "md", "markdown"].includes(extension)) {
      setError("当前支持导入 .txt、.md、.markdown 小说文本。");
      return;
    }
    const text = await file.text();
    setNovelText(text);
    setFileName(file.name);
    if (title === "示例剧本" || !title.trim()) {
      setTitle(file.name.replace(/\.(txt|md|markdown)$/i, ""));
    }
    setError("");
    setStatus("已导入文本");
  }

  async function refreshProject() {
    if (!title.trim()) return;
    setError("");
    setStatus("读取项目");
    try {
      const response = await fetch(`${API_BASE}/api/projects/${encodeURIComponent(title)}`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "项目不存在");
      }
      setProject(data);
      setStatus("已读取");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "读取失败");
      setStatus("失败");
    }
  }

  async function copyYaml() {
    if (!currentEpisode) return;
    await navigator.clipboard.writeText(currentEpisode.yaml);
    setStatus("YAML 已复制");
  }

  function downloadYaml() {
    if (!currentEpisode) return;
    const blob = new Blob([currentEpisode.yaml], { type: "text/yaml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${title}-ep${currentEpisode.episode}.yaml`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const stageItems = [
    ["小说输入", novelText.trim().length > 0],
    ["改编分析", Boolean(project?.reports.analysis)],
    ["分集规划", Boolean(project?.reports.planning)],
    ["YAML 初稿", Boolean(project?.episodes.length)],
    ["终检报告", Boolean(project?.reports.final_check)],
  ] as const;

  return (
    <main className="min-h-screen bg-[#f6f5f1] text-[#1d1d1b]">
      <div className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-4 py-4 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-[#d9d4c7] pb-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-sm font-medium text-[#6f6a5f]">N2S Novel-to-Script</div>
            <h1 className="mt-1 text-3xl font-semibold tracking-normal text-[#1d1d1b]">
              AI 辅助剧本创作工作台
            </h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill label={status} running={isRunning} />
            <button className="tool-button" onClick={refreshProject} type="button">
              <RefreshCw size={16} />
              读取项目
            </button>
            <button className="primary-button" disabled={isRunning} onClick={convertNovel} type="button">
              {isRunning ? <Loader2 className="animate-spin" size={17} /> : <Play size={17} />}
              开始转换
            </button>
          </div>
        </header>

        {error ? <div className="mt-4 rounded-md border border-[#d47b7b] bg-[#fff1f1] px-4 py-3 text-sm text-[#8c2424]">{error}</div> : null}

        <section className="grid min-h-0 flex-1 gap-4 py-4 xl:grid-cols-[420px_minmax(0,1fr)_460px]">
          <aside className="workspace-panel flex min-h-[560px] flex-col">
            <PanelTitle label="输入" detail="3 个章节以上的小说文本" />
            <div className="grid grid-cols-2 gap-3">
              <label className="field col-span-2">
                <span>项目名</span>
                <input value={title} onChange={(event) => setTitle(event.target.value)} />
              </label>
              <label className="field">
                <span>集数</span>
                <input
                  min={1}
                  max={20}
                  type="number"
                  value={episodes}
                  onChange={(event) => setEpisodes(Number(event.target.value))}
                />
              </label>
              <label className="field">
                <span>模式</span>
                <select value={mock ? "mock" : "api"} onChange={(event) => setMock(event.target.value === "mock")}>
                  <option value="mock">演示</option>
                  <option value="api">真实模型</option>
                </select>
              </label>
            </div>
            <div className="mt-3 rounded-md border border-[#d9d4c7] bg-[#f8f5ee] p-3">
              <label className="import-button">
                <Upload size={16} />
                导入小说文件
                <input
                  accept=".txt,.md,.markdown,text/plain,text/markdown"
                  className="sr-only"
                  type="file"
                  onChange={(event) => importNovelFile(event.target.files?.[0])}
                />
              </label>
              <div className="mt-2 text-xs leading-5 text-[#777064]">
                支持 .txt / .md。建议用“第一章”“第1章”“Chapter 1”作为章节标题，至少 3 章。
                {fileName ? <span className="mt-1 block text-[#356b4f]">已导入：{fileName}</span> : null}
              </div>
            </div>
            <label className="field mt-3 flex-1">
              <span>小说文本</span>
              <textarea value={novelText} onChange={(event) => setNovelText(event.target.value)} />
            </label>
          </aside>

          <section className="workspace-panel min-h-[560px]">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <PanelTitle label="剧本 YAML" detail={currentEpisode?.path ?? "等待生成"} />
              <div className="flex gap-2">
                <button className="icon-button" disabled={!currentEpisode} onClick={copyYaml} title="复制 YAML" type="button">
                  <Clipboard size={16} />
                </button>
                <button className="icon-button" disabled={!currentEpisode} onClick={downloadYaml} title="下载 YAML" type="button">
                  <Download size={16} />
                </button>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {(project?.episodes ?? []).map((episode) => (
                <button
                  className={episode.episode === currentEpisode?.episode ? "segment active" : "segment"}
                  key={episode.episode}
                  onClick={() => setActiveEpisode(episode.episode)}
                  type="button"
                >
                  EP{episode.episode}
                </button>
              ))}
            </div>
            <pre className="yaml-preview mt-3">{currentEpisode?.yaml ?? "生成后将在这里显示 ep<N>.yaml。"}</pre>
          </section>

          <aside className="flex min-h-[560px] flex-col gap-4">
            <section className="workspace-panel">
              <PanelTitle label="阶段" detail="同步请求流程" />
              <div className="mt-3 space-y-2">
                {stageItems.map(([label, done]) => (
                  <div className="stage-row" key={label}>
                    <CheckCircle2 className={done ? "text-[#356b4f]" : "text-[#aaa394]"} size={17} />
                    <span>{label}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="workspace-panel min-h-0 flex-1">
              <PanelTitle label="报告" detail={project?.project_dir ?? "outputs/{剧本名}"} />
              <div className="mt-3 flex flex-wrap gap-2">
                {reportTabs.map(([key, label]) => (
                  <button
                    className={activeReport === key ? "segment active" : "segment"}
                    key={key}
                    onClick={() => setActiveReport(key)}
                    type="button"
                  >
                    {label}
                  </button>
                ))}
              </div>
              <pre className="report-preview mt-3">
                {project?.reports[activeReport] || "对应阶段完成后，报告会显示在这里。"}
              </pre>
            </section>
          </aside>
        </section>
      </div>
    </main>
  );
}

function PanelTitle({ label, detail }: { label: string; detail: string }) {
  return (
    <div className="mb-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-[#1d1d1b]">
        <FileText size={16} />
        {label}
      </div>
      <div className="mt-1 truncate text-xs text-[#777064]">{detail}</div>
    </div>
  );
}

function StatusPill({ label, running }: { label: string; running: boolean }) {
  return (
    <div className="inline-flex h-9 items-center gap-2 rounded-md border border-[#d9d4c7] bg-[#fffdf8] px-3 text-sm text-[#575247]">
      {running ? <Loader2 className="animate-spin" size={15} /> : <span className="h-2 w-2 rounded-full bg-[#356b4f]" />}
      {label}
    </div>
  );
}

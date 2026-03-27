import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Check, X, Copy, Zap, Activity, ShieldAlert, GitPullRequest, MessageSquare, FileCode, ExternalLink, GitMerge, Clock, GitCommit, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useResolveRepo, usePRDetail as usePRDetailQuery, usePRReviewData, usePRComments, useTriggerReview } from '../hooks/useApiCache';


// GitHub-style markdown + HTML renderer
function MarkdownBody({ children }) {
  if (!children) return null;


  // Strip bot noise that can't render meaningfully:
  // - <details>...</details> blocks (bot footer badges/signatures)
  // - <!-- HTML comments --> (bot metadata)
  // - <picture> and <source> (external SVG grade images - won't display in app)
  const cleaned = children
    .replace(/<details[\s\S]*?<\/details>/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<picture[\s\S]*?<\/picture>/gi, '')
    .replace(/<source[^>]*\/?>/gi, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();


  if (!cleaned) return null;


  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw]}
      components={{
        // Headings
        h1: ({ children }) => <h1 className="text-base font-bold text-[#E6EDF3] mt-4 mb-2 pb-2 border-b border-[#21262D]">{children}</h1>,
        h2: ({ children }) => <h2 className="text-[15px] font-semibold text-[#E6EDF3] mt-4 mb-2 pb-1 border-b border-[#21262D]">{children}</h2>,
        h3: ({ children }) => <h3 className="text-sm font-semibold text-[#E6EDF3] mt-3 mb-1">{children}</h3>,
        h4: ({ children }) => <h4 className="text-sm font-medium text-[#E6EDF3] mt-2 mb-1">{children}</h4>,
        // Paragraph
        p: ({ children }) => <p className="text-sm text-[#E6EDF3] leading-relaxed my-1">{children}</p>,
        // Bold / Italic
        strong: ({ children }) => <strong className="font-semibold text-[#E6EDF3]">{children}</strong>,
        em: ({ children }) => <em className="italic text-[#E6EDF3]">{children}</em>,
        // Code — detect block vs inline by presence of language class
        code: ({ className, children }) => {
          const lang = (className || '').replace('language-', '');
          if (!lang) {
            // Inline code
            return (
              <code className="text-xs bg-[#161B22] px-1.5 py-0.5 rounded border border-[#30363D] font-mono text-[#e3b341]">
                {children}
              </code>
            );
          }
          // Fenced code block with syntax highlighting
          const codeString = String(children).replace(/\n$/, '');
          return (
            <div className="my-3 rounded-md overflow-hidden border border-[#30363D] text-[13px]">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-[#161B22] border-b border-[#30363D]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#f85149]/60"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-[#d29922]/60"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-[#3fb950]/60"></span>
                <span className="ml-2 text-[11px] font-mono text-[#8B949E]">{lang}</span>
              </div>
              <SyntaxHighlighter
                language={lang || 'text'}
                style={oneDark}
                showLineNumbers={codeString.split('\n').length > 3}
                lineNumberStyle={{ color: '#484F58', fontSize: '11px', minWidth: '2.5em', paddingRight: '1em', userSelect: 'none' }}
                customStyle={{
                  margin: 0,
                  padding: '1rem',
                  background: '#0D1117',
                  fontSize: '12px',
                  lineHeight: '1.6',
                  borderRadius: 0,
                }}
                codeTagProps={{ style: { fontFamily: 'ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace' } }}
              >
                {codeString}
              </SyntaxHighlighter>
            </div>
          );
        },
        pre: ({ children }) => <>{children}</>,
        // Blockquote
        blockquote: ({ children }) => (
          <div className="border-l-[3px] border-[#3d444d] pl-4 py-0.5 my-2">
            <div className="text-sm text-[#8B949E] leading-relaxed">{children}</div>
          </div>
        ),
        // Lists
        ul: ({ children }) => <ul className="my-2 space-y-1 pl-2">{children}</ul>,
        ol: ({ children }) => <ol className="my-2 space-y-1 pl-2 list-decimal list-inside">{children}</ol>,
        li: ({ children }) => (
          <li className="flex gap-2 text-sm text-[#E6EDF3] leading-relaxed">
            <span className="text-[#8B949E] shrink-0 select-none">•</span>
            <span className="flex-1">{children}</span>
          </li>
        ),
        // Horizontal rule
        hr: () => <hr className="border-[#21262D] my-3" />,
        // Links
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer"
            className="text-[#58a6ff] hover:underline break-words">
            {children}
          </a>
        ),
        // img — hide external badge images (grade SVGs etc)
        img: ({ src, alt }) => {
          if (!src) return null;
          return <img src={src} alt={alt || ''} className="inline h-5 max-h-5 align-middle" />;
        },
        // Tables — both GFM and raw HTML tables
        table: ({ children }) => (
          <div className="overflow-x-auto my-3 rounded-md border border-[#30363D]">
            <table className="w-full text-sm border-collapse">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-[#161B22]">{children}</thead>,
        tbody: ({ children }) => <tbody className="divide-y divide-[#21262D]">{children}</tbody>,
        tr: ({ children }) => <tr className="hover:bg-[#161B22]/50 transition-colors">{children}</tr>,
        th: ({ children }) => <th className="px-4 py-2 text-left text-xs font-semibold text-[#8B949E] border-b border-[#30363D]">{children}</th>,
        td: ({ children }) => <td className="px-4 py-2.5 text-sm text-[#E6EDF3] align-top">{children}</td>,
      }}
    >
      {cleaned}
    </ReactMarkdown>
  );
}


export default function PRDetail() {
  const { repoName, prId } = useParams();
  const { owner: repoOwner, repo } = useResolveRepo(repoName);
  const { data: prData = null, isLoading: prLoading } = usePRDetailQuery(repoOwner, repo, prId);
  const { data: reviewData = null, isLoading: reviewLoading } = usePRReviewData(repoOwner, repo, prId);
  const { data: comments = [], isLoading: commentsLoading, isError: commentsError } = usePRComments(repoOwner, repo, prId);
  const loading = prLoading || reviewLoading || commentsLoading;
  const [activeTab, setActiveTab] = useState('conversation');
  const triggerReview = useTriggerReview();
  const [isTriggering, setIsTriggering] = useState(false);


  const handleTriggerReview = async () => {
    setIsTriggering(true);
    try {
      await triggerReview.mutateAsync({
        owner: repoOwner,
        repo,
        prNumber: parseInt(prId),
        commitSha: prData?.head_sha,
      });
      alert(`✓ Review triggered for PR #${prId}`);
    } catch (error) {
      alert(`✗ Failed to trigger review: ${error.message}`);
    } finally {
      setIsTriggering(false);
    }
  };


  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins} minutes ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} hours ago`;
    const days = Math.floor(hours / 24);
    return `${days} days ago`;
  };






  if (loading) {
    return (
      <div className="flex items-center justify-center bg-[#0D1117] h-[calc(100vh-130px)] text-[#8B949E] text-sm">
        <GitPullRequest size={20} className="animate-pulse mr-2" /> Loading PR details...
      </div>
    );
  }


  const prTitle = prData?.title || 'PR Review';
  const prState = prData?.state || 'open';
  const hasReview = reviewData?.has_review || false;
  const feedbackIssues = reviewData?.feedback || [];
  const reviewSummaries = reviewData?.review_summaries || {};
  const dimensions = reviewData?.dimensions || {};
  const overallGrade = reviewData?.overall_grade || '-';
  const focusArea = reviewData?.focus_area || 'None';
  const summary = reviewData?.summary || {};
  const files = prData?.files || [];


  // Grade bar renderer
  const GradeBar = ({ grade }) => {
    const gradeColors = { A: '#3fb950', B: '#d29922', C: '#f0883e', D: '#f85149' };
    if (grade === '-') return <span className="text-xs font-mono text-[#484F58]">—</span>;
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 rounded-md text-xs font-bold font-mono text-[#0D1117]"
        style={{ backgroundColor: gradeColors[grade] || '#484F58' }}>
        {grade}
      </span>
    );
  };


  const tabs = [
    { id: 'conversation', label: 'Conversation', icon: <MessageSquare size={14} />, count: comments.length },
    { id: 'feedback', label: 'Feedback', icon: <Zap size={14} />, count: feedbackIssues.length },
    { id: 'changes', label: 'Files changed', icon: <FileCode size={14} />, count: files.length },
  ];


  // GitHub-style comment card component
  const CommentCard = ({ comment, action = 'commented', showAvatar = true }) => {


    const isBot = comment.author?.includes('[bot]') || comment.author?.includes('bot');


    return (
      <div className="flex gap-3">
        {/* Avatar + timeline connector */}
        {showAvatar && (
          <div className="flex flex-col items-center shrink-0">
            {comment.author_avatar ? (
              <img src={comment.author_avatar} alt={comment.author}
                className={`w-10 h-10 rounded-full border-2 ${isBot ? 'border-[#388bfd]' : 'border-[#30363D]'}`} />
            ) : (
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium ${isBot ? 'bg-[#388bfd]/20 text-[#58a6ff] border-2 border-[#388bfd]' : 'bg-[#21262D] text-[#8B949E] border-2 border-[#30363D]'
                }`}>
                {(comment.author || '?')[0].toUpperCase()}
              </div>
            )}
          </div>
        )}


        {/* Comment bubble */}
        <div className="flex-1 min-w-0">
          <div className="rounded-md border border-[#30363D] overflow-hidden">
            {/* Header bar */}
            <div className="flex items-center gap-2 px-4 py-2 bg-[#161B22] border-b border-[#30363D] text-sm">
              <span className="font-semibold text-[#E6EDF3] hover:underline cursor-pointer">{comment.author}</span>
              {isBot && (
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-[#388bfd]/10 border border-[#388bfd]/30 text-[#58a6ff]">bot</span>
              )}
              {comment.author === repoOwner && (
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full border border-[#30363D] text-[#8B949E] bg-[#21262D]">Owner</span>
              )}
              {comment.author === prData?.author && (
                <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full border border-[#30363D] text-[#8B949E] bg-[#21262D]">Author</span>
              )}
              <span className="text-[#8B949E]">{action}</span>
              <span className="text-[#8B949E]" title={comment.created_at}>{timeAgo(comment.created_at)}</span>
              <div className="ml-auto flex items-center gap-1">
                {comment.html_url && (
                  <a href={comment.html_url} target="_blank" rel="noopener noreferrer"
                    className="text-[#8B949E] hover:text-[#58a6ff] p-1 rounded hover:bg-[#21262D] transition-colors"
                    title="View on GitHub">
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>
            </div>
            {/* Body */}
            <div className="px-5 py-4 bg-[#0D1117] prose-sm">
              <MarkdownBody>{comment.body}</MarkdownBody>
            </div>
          </div>
        </div>
      </div>
    );
  };


  return (
    <div className="bg-[#0D1117] h-[calc(100vh-130px)] overflow-hidden">
      <div className="max-w-[1400px] w-full mx-auto px-6 py-5 flex flex-col h-full overflow-hidden">

        {/* Header */}
        <div className="shrink-0 mb-4">
          <div className="flex items-start gap-3 mb-3">
            <Link to={`/repositories/${repoName}/pull-requests`}
              className="text-[#8B949E] hover:text-white transition-colors mt-1.5 shrink-0">
              <ArrowLeft size={18} />
            </Link>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl font-semibold text-[#E6EDF3] leading-tight">{prTitle}</h1>
                <span className="text-xl text-[#8B949E] font-light">#{prId}</span>
              </div>
              <div className="flex items-center gap-3 mt-2">
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${prState === 'open'
                  ? 'bg-[#238636]/20 text-[#3fb950] border border-[#238636]/40'
                  : prData?.merged
                    ? 'bg-[#8957e5]/20 text-[#a371f7] border border-[#8957e5]/40'
                    : 'bg-[#da3633]/20 text-[#f85149] border border-[#da3633]/40'
                  }`}>
                  {prState === 'open'
                    ? <><GitPullRequest size={12} /> Open</>
                    : prData?.merged
                      ? <><GitMerge size={12} /> Merged</>
                      : <><X size={12} /> Closed</>
                  }
                </span>
                <span className="text-sm text-[#8B949E]">
                  <span className="font-medium text-[#E6EDF3]">{prData?.author || 'unknown'}</span>
                  {' '}wants to merge into{' '}
                  <code className="text-xs bg-[#161B22] px-1.5 py-0.5 rounded-md font-mono text-[#58a6ff] border border-[#30363D]">{prData?.base_branch || 'main'}</code>
                </span>
                <div className="ml-auto flex items-center gap-2">
                  {/* Trigger Review Button */}
                  <button
                    onClick={handleTriggerReview}
                    disabled={isTriggering}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-[#238636] hover:bg-[#2ea043] border border-[#238636] rounded-md text-xs text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Trigger AI Review"
                  >
                    {isTriggering ? (
                      <>
                        <Loader2 size={12} className="animate-spin" />
                        Triggering...
                      </>
                    ) : (
                      <>
                        <Zap size={12} />
                        Trigger Review
                      </>
                    )}
                  </button>

                  {/* GitHub Link */}
                  {prData?.html_url && (
                    <a href={prData.html_url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-[#21262D] border border-[#30363D] hover:bg-[#30363D] rounded-md text-xs text-[#8B949E] hover:text-[#E6EDF3] font-medium transition-colors">
                      <ExternalLink size={12} /> GitHub
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
          <div className="border-b border-[#21262D]"></div>
        </div>


        {/* Two-column layout: Main content + Right sidebar */}
        <div className="flex gap-6 flex-1 min-h-0 overflow-hidden">

          {/* Main content area (wide) */}
          <div className="flex-1 min-w-0 flex flex-col overflow-hidden">

            {/* Tab bar - GitHub style */}
            <div className="flex items-center gap-0 border-b border-[#21262D] shrink-0 mb-4">
              {tabs.map(tab => (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-[1px] ${activeTab === tab.id
                    ? 'border-[#f78166] text-[#E6EDF3] bg-[#161B22]'
                    : 'border-transparent text-[#8B949E] hover:text-[#E6EDF3] hover:border-[#30363D]'
                    }`}
                >
                  {tab.icon}
                  {tab.label}
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${activeTab === tab.id ? 'bg-[#388bfd]/20 text-[#58a6ff]' : 'bg-[#21262D] text-[#8B949E]'
                    }`}>{tab.count}</span>
                </button>
              ))}
            </div>


            {/* Scrollable tab content */}
            <div className="flex-1 overflow-y-auto min-h-0 pr-2" style={{ scrollbarWidth: 'thin', scrollbarColor: '#30363D #0D1117' }}>


              {/* Conversation Tab — GitHub-style timeline */}
              {activeTab === 'conversation' && (
                <div className="pb-6">
                  {commentsError ? (
                    <div className="flex flex-col items-center justify-center py-16 text-[#8B949E] text-sm gap-3">
                      <MessageSquare size={32} className="opacity-30" />
                      <span>Could not load comments.</span>
                      {prData?.html_url && (
                        <a href={`${prData.html_url}#discussion_bucket`} target="_blank" rel="noopener noreferrer"
                          className="flex items-center gap-1.5 text-[#58a6ff] text-xs hover:underline">
                          <ExternalLink size={12} /> View on GitHub
                        </a>
                      )}
                    </div>
                  ) : comments.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-16 text-[#8B949E] gap-3">
                      <MessageSquare size={32} className="opacity-30" />
                      <span className="text-sm">No review conversation yet.</span>
                      {prData?.html_url && (
                        <a href={`${prData.html_url}#discussion_bucket`} target="_blank" rel="noopener noreferrer"
                          className="flex items-center gap-1.5 text-[#58a6ff] text-xs hover:underline">
                          <ExternalLink size={12} /> View on GitHub
                        </a>
                      )}
                    </div>
                  ) : (
                    <div className="relative">
                      {/* Vertical timeline line */}
                      <div className="absolute left-[19px] top-10 bottom-0 w-[2px] bg-[#21262D]"></div>


                      <div className="space-y-4">
                        {/* General comments */}
                        {comments
                          .filter(c => c.type === 'comment')
                          .map(c => (
                            <CommentCard key={c.id} comment={c} action="commented" />
                          ))
                        }


                        {/* Inline review comments grouped by file */}
                        {Object.entries(
                          comments
                            .filter(c => c.type === 'review')
                            .reduce((acc, c) => {
                              const key = c.path || 'unknown';
                              if (!acc[key]) acc[key] = [];
                              acc[key].push(c);
                              return acc;
                            }, {})
                        ).map(([filepath, fileComments]) => (
                          <div key={filepath} className="flex gap-3">
                            {/* Avatar placeholder for review group */}
                            <div className="flex flex-col items-center shrink-0">
                              <div className="w-10 h-10 rounded-full bg-[#21262D] border-2 border-[#30363D] flex items-center justify-center">
                                <FileCode size={16} className="text-[#8B949E]" />
                              </div>
                            </div>


                            <div className="flex-1 min-w-0 rounded-md border border-[#30363D] overflow-hidden">
                              {/* File header */}
                              <div className="flex items-center gap-2 px-4 py-2.5 bg-[#161B22] border-b border-[#30363D]">
                                <FileCode size={14} className="text-[#8B949E] shrink-0" />
                                <span className="text-sm font-mono text-[#58a6ff] truncate">{filepath}</span>
                                <span className="text-xs text-[#484F58] ml-auto">{fileComments.length} comment{fileComments.length > 1 ? 's' : ''}</span>
                              </div>


                              {fileComments.map((c, ci) => {
                                const isBot = c.author?.includes('[bot]') || c.author?.includes('bot');
                                return (
                                  <div key={c.id} className={ci > 0 ? 'border-t border-[#21262D]' : ''}>
                                    {/* Diff hunk */}
                                    {c.diff_hunk && (
                                      <div className="overflow-x-auto border-b border-[#21262D]" style={{ scrollbarWidth: 'thin' }}>
                                        <table className="w-full text-xs font-mono">
                                          <tbody>
                                            {c.diff_hunk.split('\n').slice(-6).map((line, li) => {
                                              const isHeader = line.startsWith('@@');
                                              const isAdd = !isHeader && line.startsWith('+');
                                              const isRemove = !isHeader && line.startsWith('-');
                                              return (
                                                <tr key={li} className={`${isAdd ? 'bg-[#1a2f1a]' : isRemove ? 'bg-[#2d1b1b]' : isHeader ? 'bg-[#161B22]' : 'bg-[#0D1117]'
                                                  }`}>
                                                  <td className={`select-none px-3 py-[1px] text-right w-10 border-r border-[#21262D] ${isAdd ? 'text-[#3fb950]/40' : isRemove ? 'text-[#f85149]/40' : 'text-[#484F58]'
                                                    }`}>
                                                    {isHeader ? '' : li}
                                                  </td>
                                                  <td className={`px-3 py-[1px] whitespace-pre ${isAdd ? 'text-[#3fb950]' : isRemove ? 'text-[#f85149]' : isHeader ? 'text-[#58a6ff]' : 'text-[#8B949E]'
                                                    }`}>
                                                    {line}
                                                  </td>
                                                </tr>
                                              );
                                            })}
                                          </tbody>
                                        </table>
                                      </div>
                                    )}
                                    {/* Review comment */}
                                    <div className="bg-[#0D1117]">
                                      <div className="flex items-center gap-2 px-4 py-2 bg-[#161B22]/60 border-b border-[#21262D] text-sm">
                                        {c.author_avatar ? (
                                          <img src={c.author_avatar} alt={c.author} className="w-5 h-5 rounded-full border border-[#30363D]" />
                                        ) : (
                                          <div className="w-5 h-5 rounded-full bg-[#21262D] flex items-center justify-center text-[10px] text-[#8B949E]">
                                            {(c.author || '?')[0].toUpperCase()}
                                          </div>
                                        )}
                                        <span className="font-semibold text-[#E6EDF3]">{c.author}</span>
                                        {isBot && (
                                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#388bfd]/10 border border-[#388bfd]/30 text-[#58a6ff]">bot</span>
                                        )}
                                        <span className="text-[#8B949E]">reviewed</span>
                                        <span className="text-[#8B949E]">{timeAgo(c.created_at)}</span>
                                        {c.line && <span className="text-xs text-[#484F58]">line {c.line}</span>}
                                        {c.html_url && (
                                          <a href={c.html_url} target="_blank" rel="noopener noreferrer"
                                            className="ml-auto text-[#8B949E] hover:text-[#58a6ff] p-0.5 rounded hover:bg-[#21262D] transition-colors">
                                            <ExternalLink size={12} />
                                          </a>
                                        )}
                                      </div>
                                      <div className="px-5 py-4 prose-sm">
                                        <MarkdownBody>{c.body}</MarkdownBody>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}


              {/* Feedback Tab */}
              {activeTab === 'feedback' && (
                <div className="pb-6">
                  {(!hasReview || (feedbackIssues.length === 0 && Object.keys(reviewSummaries.file_summaries || {}).length === 0 && Object.keys(reviewSummaries.lgtm_notes || {}).length === 0 && !reviewSummaries.markdown_summary)) ? (
                    <div className="flex flex-col items-center justify-center py-16 text-[#8B949E] text-sm gap-3">
                      <Zap size={32} className="opacity-30" />
                      {hasReview ? 'No issues found — great job!' : 'No review data available yet.'}
                    </div>
                  ) : (
                    <div className="space-y-6">

                      {/* PR Report Card */}
                      <div className="rounded-md border border-[#30363D] overflow-hidden bg-[#0D1117]">
                        <div className="flex items-center justify-between px-5 py-4 border-b border-[#30363D]">
                          <h2 className="text-xl font-bold text-[#E6EDF3]">AgenticPR Code Review</h2>
                          <GradeBar grade={overallGrade} />
                        </div>
                        <div className="px-5 py-4 text-sm text-[#8B949E] border-b border-[#30363D] leading-relaxed">
                          We reviewed changes in <code className="bg-[#161B22] border border-[#30363D] px-1.5 py-0.5 rounded text-[#E6EDF3] font-mono text-xs mx-0.5">{summary.commit_sha ? summary.commit_sha.substring(0, 7) : 'latest'}</code> on this pull request. Below is the summary for the review, and you can see the individual issues we found as inline review comments.
                        </div>
                        <div className="px-5 py-5">
                          <h3 className="text-base font-bold text-[#E6EDF3] mb-4">PR Report Card</h3>
                          <div className="grid grid-cols-[1fr_1fr] border border-[#30363D] rounded-md overflow-hidden bg-[#0D1117]">
                            <div className="p-4 border-r border-[#30363D] flex items-start justify-between">
                              <span className="font-bold text-[#E6EDF3] mt-1">Overall Grade</span>
                              <GradeBar grade={overallGrade} />
                            </div>
                            <div className="flex flex-col">
                              {['Security', 'Reliability', 'Complexity', 'Hygiene'].map((dim, idx) => {
                                const dimKey = dim.toLowerCase();
                                const dimGrade = dimensions[dimKey]?.grade || '-';
                                return (
                                  <div key={idx} className={`p-4 flex items-center justify-between ${idx !== 0 ? 'border-t border-[#30363D]' : ''}`}>
                                    <span className="font-semibold text-[#E6EDF3]">{dim}</span>
                                    <GradeBar grade={dimGrade} />
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Markdown Summary (Walkthrough & Checks) */}
                      {reviewSummaries.markdown_summary && (
                        <div className="rounded-md border border-[#30363D] overflow-hidden bg-[#0D1117]">
                          <div className="px-5 py-6 text-sm text-[#E6EDF3] leading-relaxed markdown-body">
                            <MarkdownBody>{reviewSummaries.markdown_summary}</MarkdownBody>
                          </div>
                        </div>
                      )}

                      {/* Overall File Summaries */}
                      {reviewSummaries.file_summaries && Object.keys(reviewSummaries.file_summaries).length > 0 && (
                        <div className="space-y-3">
                          <h3 className="text-sm font-semibold text-[#E6EDF3] border-b border-[#30363D] pb-2">File Summaries</h3>
                          {Object.entries(reviewSummaries.file_summaries).map(([file, summary], idx) => (
                            <div key={`fs-${idx}`} className="rounded-md border border-[#30363D] overflow-hidden bg-[#0D1117]">
                              <div className="px-4 py-2 bg-[#161B22] border-b border-[#30363D] font-mono text-xs text-[#E6EDF3]">
                                📝 {file}
                              </div>
                              <div className="px-4 py-3 text-sm text-[#8B949E] leading-relaxed">
                                {summary}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Positive Observations / LGTM */}
                      {reviewSummaries.lgtm_notes && Object.keys(reviewSummaries.lgtm_notes).length > 0 && (
                        <div className="space-y-3">
                          <h3 className="text-sm font-semibold text-[#3fb950] border-b border-[#30363D] pb-2">Positive Observations</h3>
                          {Object.entries(reviewSummaries.lgtm_notes).map(([file, note], idx) => (
                            <div key={`lgtm-${idx}`} className="rounded-md border border-[#2ea043]/30 overflow-hidden bg-[#0D1117]">
                              <div className="px-4 py-2 bg-[#2ea043]/10 border-b border-[#2ea043]/20 font-mono text-xs text-[#3fb950]">
                                ✨ {file}
                              </div>
                              <div className="px-4 py-3 text-sm text-[#8B949E] leading-relaxed">
                                {note}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Actionable Findings / Nitpicks */}
                      {feedbackIssues.length > 0 && (
                        <div className="space-y-3">
                          <h3 className="text-sm font-semibold text-[#E6EDF3] border-b border-[#30363D] pb-2">Review Findings</h3>
                          {feedbackIssues.map((issue, idx) => (
                            <div key={`issue-${idx}`} className="rounded-md border border-[#30363D] overflow-hidden">
                              <div className="flex items-start gap-3 px-4 py-3 bg-[#161B22]">
                                <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${issue.category?.toLowerCase().includes('security') || issue.category?.toLowerCase().includes('bug') ? 'bg-[#da3633]/20 text-[#f85149]' :
                                  issue.category?.toLowerCase().includes('nitpick') || issue.category?.toLowerCase().includes('style') ? 'bg-[#3fb950]/20 text-[#3fb950]' :
                                    'bg-[#d29922]/20 text-[#d29922]'
                                  }`}>
                                  {issue.category?.toLowerCase().includes('security') || issue.category?.toLowerCase().includes('bug') ? <AlertTriangle size={12} /> :
                                    issue.category?.toLowerCase().includes('nitpick') || issue.category?.toLowerCase().includes('style') ? <CheckCircle2 size={12} /> :
                                      <Zap size={12} />}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex flex-wrap items-center gap-2 mb-1">
                                    <h4 className="text-sm font-semibold text-[#E6EDF3] leading-snug">{issue.title}</h4>
                                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border border-[#30363D] text-[#8B949E]">
                                      {issue.category}
                                    </span>
                                  </div>
                                  {issue.file && (
                                    <div className="text-xs font-mono text-[#8B949E] opacity-80">
                                      {issue.file}{issue.line ? `:${issue.line}` : ''}
                                    </div>
                                  )}
                                </div>
                              </div>
                              <div className="px-4 py-3 bg-[#0D1117] text-sm text-[#8B949E] leading-relaxed border-t border-[#21262D]">
                                <MarkdownBody>{issue.description}</MarkdownBody>
                                {issue.original_code && issue.suggestion && (
                                  <div className="mt-3 pt-3 border-t border-[#21262D]">
                                    <div className="text-xs font-semibold text-[#E6EDF3] mb-2">Suggested Fix</div>
                                    <div className="bg-[#161B22] rounded overflow-hidden text-xs font-mono">
                                      <div className="px-3 py-1.5 bg-[#da3633]/10 text-[#f85149] border-l-2 border-[#da3633] whitespace-pre-wrap">-{issue.original_code}</div>
                                      <div className="px-3 py-1.5 bg-[#238636]/10 text-[#3fb950] border-l-2 border-[#238636] whitespace-pre-wrap">+{issue.suggestion}</div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}


              {/* Changes Tab */}
              {activeTab === 'changes' && (
                <div className="pb-6">
                  {files.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-16 text-[#8B949E] text-sm gap-3">
                      <FileCode size={32} className="opacity-30" />
                      No file changes found.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {files.map((f, idx) => (
                        <div key={idx} className="rounded-md border border-[#30363D] overflow-hidden">
                          <div className="flex items-center justify-between px-4 py-2.5 bg-[#161B22] border-b border-[#30363D]">
                            <div className="flex items-center gap-2">
                              <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${f.status === 'added' ? 'bg-[#238636]/20 text-[#3fb950]' :
                                f.status === 'removed' ? 'bg-[#da3633]/20 text-[#f85149]' :
                                  'bg-[#d29922]/20 text-[#d29922]'
                                }`}>{f.status === 'modified' ? 'M' : f.status === 'added' ? 'A' : f.status === 'removed' ? 'D' : f.status?.[0]?.toUpperCase() || '?'}</span>
                              <span className="text-sm font-mono text-[#E6EDF3]">{f.filename}</span>
                            </div>
                            <div className="flex items-center gap-2 text-xs font-mono">
                              <span className="text-[#3fb950]">+{f.additions}</span>
                              <span className="text-[#f85149]">-{f.deletions}</span>
                            </div>
                          </div>
                          {f.patch && (
                            <pre className="px-4 py-2 text-xs font-mono text-[#8B949E] bg-[#0D1117] overflow-x-auto max-h-56 leading-relaxed"
                              style={{ scrollbarWidth: 'thin', scrollbarColor: '#30363D #0D1117' }}>
                              {f.patch.split('\n').map((line, i) => (
                                <div key={i} className={`px-1 ${line.startsWith('+') ? 'text-[#3fb950] bg-[#1a2f1a]' :
                                  line.startsWith('-') ? 'text-[#f85149] bg-[#2d1b1b]' :
                                    line.startsWith('@@') ? 'text-[#58a6ff] bg-[#161B22]' : ''
                                  }`}>{line}</div>
                              ))}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}


            </div>
          </div>


          {/* Right Sidebar — Summary + Dimensions */}
          <div className="w-[300px] shrink-0 overflow-y-auto pl-6 border-l border-[#21262D]"
            style={{ scrollbarWidth: 'thin', scrollbarColor: '#30363D #0D1117' }}>


            {/* Summary section */}
            <div className="mb-6">
              <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-4">Summary</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm">
                  <Clock size={14} className="text-[#484F58] shrink-0" />
                  <span className="text-[#8B949E]">
                    {hasReview ? `Reviewed ${timeAgo(summary.created_at)}` : `Created ${timeAgo(prData?.created_at)}`}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <GitCommit size={14} className="text-[#484F58] shrink-0" />
                  <span className="text-[#8B949E] font-mono text-xs truncate">
                    {(summary.commit_sha || prData?.head_sha || '').slice(0, 8)}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  {hasReview ? (
                    <>
                      <div className={`w-2 h-2 rounded-full shrink-0 ${summary.status === 'success' ? 'bg-[#3fb950]' : summary.status === 'failure' ? 'bg-[#f85149]' : 'bg-[#d29922]'
                        }`}></div>
                      <span className={`${summary.status === 'success' ? 'text-[#3fb950]' : summary.status === 'failure' ? 'text-[#f85149]' : 'text-[#d29922]'
                        }`}>
                        {summary.status === 'success' ? 'Review completed' : summary.status === 'failure' ? 'Review failed' : 'Review in progress'}
                      </span>
                    </>
                  ) : (
                    <>
                      <div className="w-2 h-2 rounded-full bg-[#484F58] shrink-0"></div>
                      <span className="text-[#8B949E]">No review yet</span>
                    </>
                  )}
                </div>
                {(prData?.additions > 0 || prData?.deletions > 0) && (
                  <div className="flex items-center gap-2 text-sm pt-1">
                    <FileCode size={14} className="text-[#484F58] shrink-0" />
                    <span className="text-[#3fb950] font-mono text-xs">+{prData.additions}</span>
                    <span className="text-[#f85149] font-mono text-xs">-{prData.deletions}</span>
                    <span className="text-[#8B949E] text-xs">{prData.changed_files} files</span>
                  </div>
                )}
              </div>
            </div>


            <div className="border-t border-[#21262D] my-4"></div>


            {/* Quality Overview */}
            <div className="mb-6">
              <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-4">Quality</h3>
              <div className="bg-[#161B22] border border-[#30363D] rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-sm text-[#E6EDF3]">Overall Grade</span>
                  <GradeBar grade={overallGrade} />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-[#E6EDF3]">Focus Area</span>
                  <span className="text-xs text-[#8B949E] bg-[#21262D] px-2 py-0.5 rounded">{focusArea}</span>
                </div>
              </div>
            </div>


            <div className="border-t border-[#21262D] my-4"></div>


            {/* Dimensions */}
            <div>
              <h3 className="text-xs font-semibold text-[#8B949E] uppercase tracking-wider mb-4">Dimensions</h3>
              <div className="space-y-2">
                {[
                  { key: 'security', label: 'Security', icon: <ShieldAlert size={14} /> },
                  { key: 'reliability', label: 'Reliability', icon: <Activity size={14} /> },
                  { key: 'complexity', label: 'Complexity', icon: <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><path d="M3.79163 2.33337C4.22913 2.33337 4.97288 2.33337 5.25404 3.8095C5.53871 5.30254 5.63788 6.66404 6.12496 7.00004C5.63788 7.33604 5.53871 8.69754 5.25404 10.1906C4.97288 11.667 4.22913 11.6667 3.79163 11.6667M10.2083 11.6667C9.77079 11.6667 9.02704 11.667 8.74588 10.1906C8.46121 8.69754 8.36204 7.33604 7.87496 7.00004C8.36204 6.66404 8.46121 5.30254 8.74588 3.8095C9.02704 2.33337 9.77079 2.33337 10.2083 2.33337" stroke="currentColor" strokeWidth="1.16667" strokeLinecap="round" strokeLinejoin="round" /></svg> },
                  { key: 'hygiene', label: 'Hygiene', icon: <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1.51225 9.31996C1.90425 7.84996 3.10271 6.70837 4.62404 6.70837C6.05175 6.70837 7.00521 7.999 6.97371 9.42671L6.95708 10.176C6.95085 10.4551 7.00191 10.7325 7.10711 10.991C7.21231 11.2496 7.36941 11.4838 7.56871 11.6792L7.89129 11.996C8.35387 12.4501 8.08379 13.228 7.43775 13.2817C6.60183 13.3508 5.56817 13.4167 4.66662 13.4167C3.50521 13.4167 2.34408 13.3073 1.61871 13.2225C1.18937 13.1723 0.872624 12.806 0.913749 12.376C1.00708 11.3952 1.25617 10.2795 1.51225 9.31996Z" stroke="currentColor" strokeWidth="0.875" strokeLinecap="round" strokeLinejoin="round" /></svg> },
                  { key: 'coverage', label: 'Coverage', icon: <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 7.4375V11.8125C7 12.0446 6.90781 12.2671 6.74372 12.4312C6.57962 12.5953 6.35706 12.6875 6.125 12.6875C5.89294 12.6875 5.67038 12.5953 5.50628 12.4312C5.34219 12.2671 5.25 12.0446 5.25 11.8125M7 7.4375L6.73504 7.23871C6.32287 6.92964 5.81306 6.77959 5.29918 6.8161C4.78529 6.85262 4.30182 7.07325 3.9375 7.4375C3.76514 7.26513 3.56052 7.1284 3.33532 7.03512C3.11013 6.94183 2.86876 6.89382 2.625 6.89382C2.38124 6.89382 2.13987 6.94183 1.91468 7.03512C1.68948 7.1284 1.48486 7.26513 1.3125 7.4375C1.3125 4.29625 3.85875 1.75 7 1.75M7 7.4375L7.26496 7.23871C7.67713 6.92964 8.18694 6.77959 8.70082 6.8161C9.21471 6.85262 9.69818 7.07325 10.0625 7.4375C10.2349 7.26513 10.4395 7.1284 10.6647 7.03512C10.8899 6.94183 11.1312 6.89382 11.375 6.89382C11.6188 6.89382 11.8601 6.94183 12.0853 7.03512C12.3105 7.1284 12.5151 7.26513 12.6875 7.4375C12.6875 4.29625 10.1412 1.75 7 1.75M7 1.75V1.3125" stroke="currentColor" strokeWidth="0.875" strokeLinecap="round" strokeLinejoin="round" /></svg> },
                ].map(dim => (
                  <div key={dim.key} className={`flex justify-between items-center py-2 px-3 rounded-md hover:bg-[#161B22] transition-colors ${dim.key === 'coverage' ? 'opacity-50' : ''
                    }`}>
                    <div className="flex items-center gap-2 text-sm text-[#8B949E]">
                      {dim.icon}
                      <span>{dim.label}</span>
                      {dimensions[dim.key]?.count > 0 && (
                        <span className="text-xs text-[#f85149] bg-[#f85149]/10 px-1.5 rounded-full">{dimensions[dim.key].count}</span>
                      )}
                    </div>
                    <GradeBar grade={dimensions[dim.key]?.grade || '-'} />
                  </div>
                ))}
              </div>
            </div>
          </div>


        </div>
      </div>
    </div>
  );
}





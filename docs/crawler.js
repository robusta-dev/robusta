// This is a backup of the crawler configuration for https://crawler.algolia.com/
new Crawler({
  rateLimit: 8,
  maxDepth: 10,
  maxUrls: 5000,
  startUrls: ["https://docs.robusta.dev/master/"],
  renderJavaScript: false,
  sitemaps: [],
  ignoreCanonicalTo: false,
  discoveryPatterns: ["https://docs.robusta.dev/master/**"],
  schedule: "at 13:11 on Thursday",
  actions: [
    {
      indexName: "robusta",
      pathsToMatch: ["https://docs.robusta.dev/master/**"],
      recordExtractor: ({ helpers, url }) => {
        return helpers
          .docsearch({
            recordProps: url.pathname.includes("/triggers/")
              ? {
                  lvl0: {
                    selectors: [],
                    defaultValue: "Triggers",
                  },
                  lvl1: ["article h1", "head > title"],
                  lvl2: ["details summary"],
                  content: ["details *:not(summary)"],
                  pageRank: 9,
                }
              : url.pathname.includes("/actions/")
              ? {
                  lvl0: {
                    selectors: [],
                    defaultValue: "Actions",
                  },
                  lvl1: ["article h1", "head > title"],
                  lvl2: [".admonition .admonition-title"],
                  content: [".admonition *:not(.admonition-title)"],
                  pageRank: 8,
                }
              : url.pathname.includes("/sinks/")
              ? {
                  lvl0: {
                    selectors: [],
                    defaultValue: "Sinks",
                  },
                  lvl1: ["article h1", "head > title"],
                  lvl2: ["article h2", "h2"],
                  lvl3: ["article h3", "h3"],
                  lvl4: ["article h4", "h4"],
                  lvl5: ["article h5", "h5"],
                  content: ["article p, article li, article code"],
                  pageRank: 7,
                }
              : {
                  lvl0: {
                    selectors: ["article h1", "head > title"],
                    defaultValue: "Documentation",
                  },
                  lvl1: ["article h2", "h2"],
                  lvl2: ["article h3", "h3"],
                  lvl3: ["article h4", "h4"],
                  lvl4: ["article h5", "h5"],
                  lvl5: ["article h6", "h6"],
                  content: ["article p, article li, article code"],
                  pageRank: (() => {
                    if (
                      url.pathname.includes("/installation/index.html") ||
                      url.pathname.includes("/setup-robusta/upgrade.html")
                    ) {
                      return 10;
                    }
                    return 1;
                  })(),
                },
            aggregateContent: true,
            recordVersion: "v3",
          })
          .map((record) =>
            JSON.parse(JSON.stringify(record).replaceAll("¶", ""))
          );
      },
    },
  ],
  safetyChecks: { beforeIndexPublishing: { maxLostRecordsPercentage: 30 } },
  initialIndexSettings: {
    robusta: {
      attributesForFaceting: ["type", "lang"],
      attributesToRetrieve: [
        "hierarchy",
        "content",
        "anchor",
        "url",
        "url_without_anchor",
        "type",
      ],
      attributesToHighlight: ["hierarchy", "content"],
      attributesToSnippet: ["content:10"],
      camelCaseAttributes: ["hierarchy", "content"],
      searchableAttributes: [
        "unordered(hierarchy.lvl0)",
        "unordered(hierarchy.lvl1)",
        "unordered(hierarchy.lvl2)",
        "unordered(hierarchy.lvl3)",
        "unordered(hierarchy.lvl4)",
        "unordered(hierarchy.lvl5)",
        "unordered(hierarchy.lvl6)",
        "content",
      ],
      distinct: true,
      attributeForDistinct: "url",
      customRanking: [
        "desc(weight.pageRank)",
        "desc(weight.level)",
        "asc(weight.position)",
      ],
      ranking: [
        "words",
        "filters",
        "typo",
        "attribute",
        "proximity",
        "exact",
        "custom",
      ],
      highlightPreTag: '<span class="algolia-docsearch-suggestion--highlight">',
      highlightPostTag: "</span>",
      minWordSizefor1Typo: 3,
      minWordSizefor2Typos: 7,
      allowTyposOnNumericTokens: false,
      minProximity: 1,
      ignorePlurals: true,
      advancedSyntax: true,
      attributeCriteriaComputedByMinProximity: true,
      removeWordsIfNoResults: "allOptional",
    },
  },
  appId: "EEWU58CJVX",
  apiKey: "...",
});
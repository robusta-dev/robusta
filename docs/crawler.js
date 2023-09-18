// This is the code example for the crawler configuration file for https://crawler.algolia.com/
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
          return helpers.docsearch({
            recordProps: {
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
                if (url.pathname.includes("/installation/index.html")) {
                  return 10;
                } else if (url.pathname.includes("/triggers/kubernetes.html")) {
                  return 9;
                } else if (
                  url.pathname.includes("/actions/event-enrichment.html")
                ) {
                  return 8;
                }
                return 1;
              })(),
            },
            aggregateContent: true,
            recordVersion: "v3",
          });
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
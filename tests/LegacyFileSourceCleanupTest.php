<?php

declare(strict_types=1);

namespace NeuronBook\Tests;

use NeuronAI\RAG\Document;
use NeuronAI\RAG\VectorStore\FileVectorStore;
use NeuronAI\RAG\VectorStore\SearchRequest;
use NeuronAI\Testing\FakeEmbeddingsProvider;
use NeuronBook\Ch12\LegacyFileSourceCleanup;
use PHPUnit\Framework\TestCase;
use RecursiveDirectoryIterator;
use RecursiveIteratorIterator;

final class LegacyFileSourceCleanupTest extends TestCase
{
    public function testLegacyRagAliasesAreRemovedWithoutTouchingOtherSources(): void
    {
        $directory = sys_get_temp_dir() . '/neuron-book-rag-' . getmypid();
        $corpus = $directory . '/docs';
        $storeDirectory = $directory . '/vectors';
        $storePath = $storeDirectory . '/docs.store';
        mkdir($corpus, 0777, true);
        mkdir($directory . '/run', 0777, true);
        mkdir($storeDirectory, 0777, true);
        file_put_contents($corpus . '/rag.md', 'Current RAG documentation.');

        $legacyPath = $directory . '/run/../docs/rag.md';
        $store = new FileVectorStore(directory: $storeDirectory, name: 'docs');
        $oldProvider = new FakeEmbeddingsProvider(dimensions: 5);
        $provider = new FakeEmbeddingsProvider(dimensions: 3);
        $store->addDocument($oldProvider->embedDocument(
            (new Document('Old RAG documentation.'))
                ->setSourceType('files')
                ->setSourceName($legacyPath),
        ));
        $store->addDocument($provider->embedDocument(
            (new Document('Current RAG documentation.'))
                ->setSourceType('files')
                ->setSourceName('rag.md'),
        ));
        $store->addDocument($provider->embedDocument(
            (new Document('Another corpus source.'))
                ->setSourceType('files')
                ->setSourceName('agents.md'),
        ));

        try {
            self::assertSame(1, LegacyFileSourceCleanup::removeReindexedAliases(
                $store,
                $storePath,
                $corpus,
                ['rag.md' => true],
            ));

            $matches = $store->search(new SearchRequest(
                $provider->embedText('query'),
                topK: 10,
            ));

            self::assertCount(2, $matches);
            self::assertEqualsCanonicalizing(['rag.md', 'agents.md'], array_map(
                static fn (Document $document): string => $document->getSourceName(),
                $matches,
            ));
        } finally {
            $paths = new RecursiveIteratorIterator(
                new RecursiveDirectoryIterator($directory, RecursiveDirectoryIterator::SKIP_DOTS),
                RecursiveIteratorIterator::CHILD_FIRST,
            );
            foreach ($paths as $path) {
                $path->isDir() ? rmdir($path->getPathname()) : unlink($path->getPathname());
            }
            rmdir($directory);
        }
    }
}
